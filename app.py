# import numpy as np
import os
import pandas as pd
import streamlit as st

st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D will be imported and visualized")


def process_data_file(directory, file):
    """Load file, show raw data, plot line chart"""

    st.header(file)

    file_path = os.path.join(directory, file) + ".txt"
    df = pd.read_csv(file_path, sep='\t')
    # Now 'df' is a pandas DataFrame containing the data from the file
    if st.checkbox('Show raw data', key=file):  # unique key required for the widget
        st.subheader('Raw data')
        st.write(df)

    # Remove the first 4 text rows and the Static column to get dynamic data to plot
    df = df.drop(df.index[:4])
    try:
        df = df.drop('Static.c3d', axis='columns')
    except KeyError:  # ['Static.c3d'] not found (e.g., Moment)
        pass
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.rename(columns={df.columns[0]: 'Gait cycle'}, inplace=True)
    df['Gait cycle'] -= 1

    st.line_chart(df, x='Gait cycle')


def get_all_files(directory):
    """Get all txt file names in a directory, sort by Left/Right"""

    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            f_name, f_ext = os.path.splitext(file)
            if f_ext == ".txt":
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
    st.markdown("[Gait Analysis Report](#gait-analysis-report)")
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
            sec = ""
        else:
            sec = f
            lnk = f.lower().replace(' ', '-').replace('_', '-')  
        if sec:
            st.markdown(f"[{sec}](#{lnk})")

for file in data_files:
    process_data_file(directory, file)
