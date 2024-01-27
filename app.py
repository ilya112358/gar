from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend
import csv
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(layout="wide")


@st.cache_data
def process_data_file(directory, file):
    """Load file, pre-process data, return dataframe"""

    file_path = os.path.join(directory, file)
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


@st.cache_data
def process_pair(directory, files):
    """Process data for left and right"""

    df_left = process_data_file(directory, files[1])
    df_right = process_data_file(directory, files[2])
    df_left.rename(columns={df_left.columns[-1]: 'Left Mean'}, inplace=True)
    df_right.rename(columns={df_right.columns[-1]: 'Right Mean'}, inplace=True)
    # combine Gait cycle and two Mean columns to plot both
    df_both = pd.concat([df_left.iloc[:, :1], df_left.iloc[:, -1:], df_right.iloc[:, -1:]], axis=1)

    def stats(df, col):
        idxmax = df[col].idxmax()
        max = f"{df.loc[idxmax, col]:.2f} at {df.loc[idxmax, 'Gait cycle']}%"
        idxmin = df[col].idxmin()
        min = f"{df.loc[idxmin, col]:.2f} at {df.loc[idxmin, 'Gait cycle']}%"
        return max, min
        
    stats_left = stats(df_left, 'Left Mean')
    stats_right = stats(df_right, 'Right Mean')
    df_stats = pd.DataFrame({
        'Side': ['Left', 'Right'], 
        'Maximum': [stats_left[0], stats_right[0]], 
        'Minimum': [stats_left[1], stats_right[1]]
        })
    return df_left, df_right, df_both, df_stats


def plot_widegraph(bioparameter, dfs):
    """Visualize left and right"""

    def plot_df(df, lrb):
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
            elif 'Mean' in column and lrb != 'Both':
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
    opts = ['Left', 'Right', 'Both']
    foot2plot = st.radio(f'Show plot for {bioparameter}', opts, horizontal=True, index=2)
    plot_df(dfs[opts.index(foot2plot)], foot2plot)
    st.dataframe(dfs[3], hide_index=True)

    # styles = [dict(selector="td", props=[('width', '100px'), ('text-align', 'left')])]
    # df_table = dfs[3].style.set_properties(**{'font-size': '12pt'}).set_table_styles(styles)
    # st.table(df_table)


@st.cache_data
def get_all_files(directory):
    """Get all txt file names in a directory, pair by Left/Right"""

    # read from configuration file
    config_file = 'source.csv'
    source = []
    with open(config_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Use the strip method to remove leading and trailing spaces from each element
            source.append(tuple(element.strip() for element in row))

    # for all rows in source check if row[1] and row[2] exist in directory Data
    file_pairs = []
    for row in source:
        if os.path.isfile(os.path.join(directory, row[1])) and os.path.isfile(os.path.join(directory, row[2])):
            file_pairs.append(row)
    print(f"{len(file_pairs)} pairs loaded")
    return file_pairs


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
    dfs = process_pair(directory, file)
    plot_widegraph(file[0], dfs)
