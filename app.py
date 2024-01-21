from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(layout="wide")


@st.cache_data
def process_data_file(directory, file):
    """Load file, pre-process data, return dataframe"""

    file_path = os.path.join(directory, file) + '.txt'
    df = pd.read_csv(file_path, sep='\t')
    # Now 'df' is a pandas DataFrame containing data from the file
    # Remove first 4 text rows (headers)
    df = df.drop(df.index[:4])
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.columns = df.columns.str.replace('Gait ', '')
    df.columns = df.columns.str.replace('.c3d', '')
    # The file's 1st col are numbers from 1 to 101
    df.rename(columns={df.columns[0]: 'Gait cycle'}, inplace=True)
    df['Gait cycle'] -= 1
    # Add average over dynamic walks as the last column
    df1 = df.drop('Gait cycle', axis='columns')
    try:
        df1 = df1.drop('Static', axis='columns')
    except KeyError:  # ['Static.c3d'] not found (e.g., Moment)
        pass
    df['Mean'] = df1.mean(numeric_only=True, axis=1)
    return df


def plot_graph(file, df):
    """Visualize the dataframe"""

    def plot_df(df):
        p = figure(x_axis_label='Gait cycle, %',
                   y_axis_label='Degrees', 
                   height=400,
                   width=600,
                   tools = 'box_zoom, reset',
                   tooltips = '[$name] @$name{0.00} at @{Gait cycle}')  # [Mean] -0.77 at 33
        p.border_fill_color = 'seashell'
        lines, labels = [], []
        for col in range(1, len(df.columns)):
            column = df.columns[col]
            if column == 'Static':
                color = 'orange'
            elif column == 'Mean':
                color = 'black'
            else:
                color = ['red', 'green', 'blue', 'cyan'][col-1]
            line = p.line('Gait cycle', column, source=ColumnDataSource(df), color=color, name=column)
            lines.append(line)
            labels.append((column, [line]))
        legend = Legend(items=labels, location='center')
        legend.orientation = 'horizontal'
        legend.border_line_color = 'black'
        p.add_layout(legend, 'above')        
        components.html(file_html(p, 'cdn', ), height=400, width=600)
        #st.line_chart(df, x='Gait cycle')
    
    st.header(file)
    if st.checkbox(f"Show source data for {file}"):
        st.dataframe(df, hide_index=True)
    df1 = df[['Gait cycle', 'Mean']]
    df2 = df.drop('Mean', axis='columns')
    if st.checkbox(f"Check consistecy for {file}"):
        st.markdown(f':blue[{df2.shape[1]-2} dynamic and 1 static]')
        plot_df(df2)
    else:
        stats = df['Mean'].describe()
        idmx = df['Mean'].idxmax()
        s_mx = f"Max: {stats['max']:.2f} at {df.loc[idmx, 'Gait cycle']}%"
        idmn = df['Mean'].idxmin()
        s_mn = f"Min: {stats['min']:.2f} at {df.loc[idmn, 'Gait cycle']}%"
        stats = f"{s_mx}, {s_mn}, Range: {stats['max']-stats['min']:.2f}"
        st.markdown(f':blue[{stats}]')
        plot_df(df1)


def plot_widegraph(bioparameter, df1, df2):
    """Visualize the dataframe"""

    def plot_df(df):
        size = {'height': 600, 'width': 1000}
        p = figure(x_axis_label='Gait cycle, %',
                   y_axis_label='Degrees', 
                   height=size['height'],
                   width=size['width'],
                   tools = 'box_zoom, reset',
                   tooltips = '[$name] @$name{0.00} at @{Gait cycle}')  # [Mean] -0.77 at 33
        p.border_fill_color = 'seashell'
        lines, labels = [], []
        for col in range(1, len(df.columns)):
            column = df.columns[col]
            if column == 'Static':
                color = 'orange'
            elif column == 'Mean':
                color = 'black'
            else:
                color = ['red', 'blue', 'green', 'cyan', 'fuchsia', 'blueviolet', 'brown'][col-1]
            if 'Mean' in column:
                width = 3
            else:
                width = 1
            line = p.line('Gait cycle', column, source=ColumnDataSource(df), 
                          color=color, width=width, name=column)
            lines.append(line)
            labels.append((column, [line]))
        legend = Legend(items=labels, location='center')
        legend.orientation = 'horizontal'
        legend.border_line_color = 'black'
        p.add_layout(legend, 'above')        
        components.html(file_html(p, 'cdn', ), height=size['height'], width=size['width'])

    st.header(bioparameter)
    foot2plot = st.radio(f'Show plot for {bioparameter}', ['Left', 'Right', 'Both'], 
                         horizontal=True, index=2)
    match foot2plot:
        case 'Both':
            # combine the first (Gait cycle) and two last (Mean) columns
            df1.rename(columns={df1.columns[-1]: 'Left Mean'}, inplace=True)
            df2.rename(columns={df2.columns[-1]: 'Right Mean'}, inplace=True)
            new_df = pd.concat([df1.iloc[:, :1], df1.iloc[:, -1:], df2.iloc[:, -1:]], axis=1)
        case 'Left':
            new_df = df1
        case 'Right':
            new_df = df2
    plot_df(new_df)


@st.cache_data
def get_all_files(directory):
    """Get all txt file names in a directory, pair by Left/Right"""

    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            f_name, f_ext = os.path.splitext(file)
            if f_ext == '.txt':
                file_paths.append(f_name)
    file_paths.sort()
    filesL = [f for f in file_paths if f.startswith('L')]
    filesR = [f for f in file_paths if f.startswith('R')]
    filesOther = [f for f in file_paths if (f not in filesR) and (f not in filesL)]
    files_pairs = []
    for i in range(len(filesL)):
        fL = filesL[i]
        fR = filesR[i]
        if fL.startswith('L_'):
            section = fL[2:]
        elif fL.startswith('Left '):
            section = fL[5:]
        if not fR.endswith(section):
            st.write(f"Error! Check file names [{fL}] and [{fR}] for inconsistency")
            exit(1)
        files_set = (section, fL, fR)
        files_pairs.append(files_set) 
    files = files_pairs + filesOther
    return files


directory = 'Data'
data_files = get_all_files(directory)

st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D gets visualized")

with st.sidebar:
    st.markdown("[Go to the Top](#gait-analysis-report)")
    st.subheader("Sections list")
    for f in data_files:
        if type(f) == tuple:
            section = f[0]
        else:
            section = f
        lnk = section.lower().replace(' ', '-').replace('_', '-')  # slugify
        st.markdown(f"[{section}](#{lnk})")
    if st.button("Clear Cache"):
        st.cache_data.clear()

for file in data_files:
    if type(file) == tuple:
            df1 = process_data_file(directory, file[1])
            df2 = process_data_file(directory, file[2])
            plot_widegraph(file[0], df1, df2)
    else:
        df = process_data_file(directory, file)
        plot_graph(file, df)
