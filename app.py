import numpy as np
import pandas as pd
import streamlit as st

st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D will be "
        "imported and visualized")

# LOAD

# Specify the file path
file_path = 'Data/Left Ankle Angles.txt'
st.header(f"{file_path}")

# Load the tab-delimited file
df = pd.read_csv(file_path, sep='\t')
# Now 'df' is a pandas DataFrame containing the data from the file

# Remove the first 4 text rows and the Static column
df = df.drop(df.index[:4])
df = df.drop('Static.c3d', axis='columns')
# df.reset_index(drop=True, inplace=True)
 
df.rename(columns={df.columns[0]: 'Gait cycle'}, inplace=True)
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# DISPLAY

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(df)
st.line_chart(df, x='Gait cycle')
