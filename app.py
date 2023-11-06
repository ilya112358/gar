import numpy as np
import os
import pandas as pd
import streamlit as st

st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D will be imported and visualized")

def process_data_file(file_path):
    """Load file, show raw data, plot line chart"""

    filename_with_extension = os.path.basename(file_path)
    filename_without_extension = os.path.splitext(filename_with_extension)[0]
    st.header(filename_without_extension)

    df = pd.read_csv(file_path, sep='\t')
    # Now 'df' is a pandas DataFrame containing the data from the file
    if st.checkbox('Show raw data', key=filename_without_extension):  # unique key required for the widget
        st.subheader('Raw data')
        st.write(df)

    # Remove the first 4 text rows and the Static column to get dynamic data to plot
    df = df.drop(df.index[:4])
    try:
        df = df.drop('Static.c3d', axis='columns')
    except KeyError:  # ['Static.c3d'] not found (e.g., Moment)
        pass
    # df.reset_index(drop=True, inplace=True)  # use index as gait cycle?
    df.rename(columns={df.columns[0]: 'Gait cycle'}, inplace=True)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    st.line_chart(df, x='Gait cycle')


def get_all_files(directory):
    """Use the os.walk() function to get all txt file names in a directory"""

    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1] == ".txt":
                file_paths.append(file)
    return file_paths

directory = 'Data'
file_paths = get_all_files(directory)

with st.sidebar:
    st.write(f"**{len(file_paths)}** files found in {directory} folder")
    option = st.checkbox('**Show all files**', value=True)
    if option:
        options = file_paths
    else:
        options = st.multiselect('Choose the files', file_paths)

for file in options:
    process_data_file(os.path.join(directory, file))
