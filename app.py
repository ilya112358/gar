import os
import pandas as pd
import streamlit as st

st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D will be imported and visualized")


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
    # The file's 1st col are numbers from 1 to 101
    df.rename(columns={df.columns[0]: 'Gait cycle'}, inplace=True)
    df['Gait cycle'] -= 1
    # Add average over dynamic walks as the last column
    df1 = df.drop('Gait cycle', axis='columns')
    try:
        df1 = df1.drop('Static.c3d', axis='columns')
    except KeyError:  # ['Static.c3d'] not found (e.g., Moment)
        pass
    df['Mean'] = df1.mean(numeric_only=True, axis=1)
    return df


def plot_graph(file, df):
    """Visualize the dataframe"""

    st.header(file)
    if st.checkbox(f"Show gait data for {file}"):
        st.dataframe(df, hide_index=True)
    df1 = df[['Gait cycle', 'Mean']]
    df2 = df.drop('Mean', axis='columns')
    if st.checkbox(f"Check consistecy for {file}"):
        st.line_chart(df2, x='Gait cycle')
    else:
        st.line_chart(df1, x='Gait cycle')


@st.cache_data
def get_all_files(directory):
    """Get all txt file names in a directory, sort by Left/Right"""

    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            f_name, f_ext = os.path.splitext(file)
            if f_ext == '.txt':
                file_paths.append(f_name)
    file_paths.sort()
    filesR = [f for f in file_paths if f.startswith('R')]
    filesL = [f for f in file_paths if f.startswith('L')]
    filesOther = [f for f in file_paths if (f not in filesR) and (f not in filesL)]
    assert len(filesR) == len(filesL)  # all should be paired, weak check
    files_pairs = []
    for i in range(len(filesR)):
        files_pairs.append(filesL[i])
        files_pairs.append(filesR[i])
    files = files_pairs + filesOther
    return files

directory = 'Data'
data_files = get_all_files(directory)

with st.sidebar:
    st.markdown("[Go to the Top](#gait-analysis-report)")
    st.write(f"**{len(data_files)}** files found in {directory} folder")
    # Sections list
    for f in data_files:
        if f.startswith('L'):
            if f.startswith('L_'):
                sec = f[2:]
                lnk = f.lower().replace(' ', '-').replace('_', '-')
            elif f.startswith('Left '):
                sec = f[5:]
                lnk = f.lower().replace(' ', '-').replace('_', '-') 
        elif f.startswith('R'):
            sec = ''
        else:
            sec = f
            lnk = f.lower().replace(' ', '-').replace('_', '-')  
        if sec:
            st.markdown(f"[{sec}](#{lnk})")

for file in data_files:
    df = process_data_file(directory, file)
    plot_graph(file, df)
