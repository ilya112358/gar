import streamlit as st
import importlib
import classes
importlib.reload(classes)  # reload config

def home():
    st.session_state["current_page"] = 0
    st.set_page_config(
        page_title="Gait Analysis Report", layout="wide"
    )  # not a central column
    st.image("GAR_topimage.jpg", width=512)
    st.title("Gait Analysis Report")
    st.text("where the data from Visual3D gets visualized")
    st.write("This is the multi-page web dashboard")
    st.write("👈 Use the sidebar to navigate between pages")
    st.write("- Choose **measurement one** to load and visualize data from the 1st dataset")
    st.write("- Choose **measurement two** to load and visualize data from the 2nd dataset")
    st.write("- Choose **comparison** to compare the two measurements")
    st.write("- Choose **home** and reload the page in the browser to start again")
    st.write("⬆️ Upload data exported from Visual3D or use example data for demonstration")
    st.write("📊 The following data is processed:")
    st.write("- Subject metadata")
    st.write("- Temporal and Spatial parameters")
    st.write("- Gait Profile Score")
    st.write("- Kinematics")
    st.write("⏱ At the moment, the comparison page functionality is limited")
    st.write("Write your reactions to ilya112358@gmail.com or visit GitHub repo https://github.com/ilya112358/gar")
    st.write("*(version 2025.08)*")

page_home = st.Page(home, title="Home", icon=":material/home:")
page1 = st.Page("measurement_one.py", title="Measurement One", icon=":material/counter_1:")
page2 = st.Page("measurement_two.py", title="Measurement Two", icon=":material/counter_2:")
page3 = st.Page("comparison.py", title="Compare", icon=":material/balance:")

current = st.navigation([page_home, page1, page2, page3])
current.run()
