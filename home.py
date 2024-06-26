import streamlit as st
from classes import c

st.session_state["current_page"] = 0
st.set_page_config(
    page_title="Gait Analysis Report", layout="wide"
)  # not a central column
st.image("GAR_topimage.jpg", width=512)
st.title("Gait Analysis Report")
st.text("where the data from Visual3D gets visualized")
st.write("This is the multi-page web dashboard.")
st.write("👈 Use the sidebar to navigate between pages.")
st.write("- Choose **measurement one** to load and visualize data from the 1st dataset.")
st.write("- Choose **measurement two** to load and visualize data from the 2nd dataset.")
st.write("- Choose **comparison** to compare the two measurements.")
st.write("- Choose **home** and reload the page in the browser to start again.")
st.write("⏱ At the moment:")
st.write("- only kinematic data is plotted")
st.write("- only pre-loaded data can be used on measurement pages")
st.write("- only two measurement pages")
