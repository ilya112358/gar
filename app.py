import streamlit as st
from classes import c


st.set_page_config(
    page_title="Gait Analysis Report", layout="wide"
)  # not a central column
st.image("GAR_topimage.jpg", width=512)
st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D gets visualized")
st.write("---")
st.write("<< Choose measurement page one or two to load and visualize data.")
st.write(c.kinematics)