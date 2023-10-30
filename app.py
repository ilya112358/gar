import numpy as np
import pandas as pd
import streamlit as st

st.markdown("# Gait Analysis Report")
st.write("This is where the data from Visual3D will be imported and visualized")

# Specify the file path
file_path = 'Data/Left Ankle Angles.txt'

# Load the tab-delimited file
df = pd.read_csv(file_path, sep='\t')

# Now 'df' is a pandas DataFrame containing the data from the file
file_path
# Remove the first 4 rows and the Static column
df = df.drop(df.index[:4])
df = df.drop('Static.c3d', axis='columns')
# df.reset_index(drop=True, inplace=True)

df.rename(columns={df.columns[0]: 'Gait cycle'}, inplace=True)
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df
st.line_chart(df, x='Gait cycle')
