import pandas as pd
import streamlit as st
import zipfile
from classes import DataSet, Plot, PlotLayout, Export

m = {
    "title": "measurement two",
    "dataset": "d2",
    "archive": "Archive/Data2.zip",
    "page": 2,
    "top": "[Go to the Top](#measurement-two)"
}

st.header(m["title"])
if "current_page" not in st.session_state:
    st.header("👈 Please go to Home page to start a new session!")
    st.stop()
if m["dataset"] not in st.session_state:
    uploaded_file = None
    col1, col2 = st.columns(2, vertical_alignment="center")
    with col1:
        uploaded_file = st.file_uploader("Upload a zip file", type=["zip"], key="upload")
    with col2:
        if uploaded_file is None:
            if st.button("Or use example data"):
                uploaded_file = m["archive"]
    if uploaded_file is not None:
        with zipfile.ZipFile(uploaded_file) as zf:
            # make a dict where zf.namelist() will be the keys and the values will be dfs read from the files
            d = {x: pd.read_csv(zf.open(x), sep="\t") for x in zf.namelist()}
            st.session_state[m["dataset"]] = DataSet(d)
            st.rerun()
    st.subheader("Load Measurement")
    st.write("Please upload a zip file with measurement data or use example data ☝")
else:
    st.title(st.session_state[m["dataset"]].title)
    # if page changed, reset analysis and export
    if st.session_state["current_page"] != m["page"]:
        st.session_state["current_page"] = m["page"]
        st.session_state["reset_stats"] = True
        st.session_state.pop("add_to_rep", None)
    st.header("Subject", divider=True)
    st.dataframe(st.session_state[m["dataset"]].info, hide_index=True)
    st.header("Temporal and Spatial", divider=True)
    # st.dataframe(st.session_state[m["dataset"]].ts.fillna(''), hide_index=True)  # removing None (np.nan) leads to a warning due to mixed types
    st.dataframe(st.session_state[m["dataset"]].ts, hide_index=True)
    category = st.selectbox(
        "You can choose the category of biomechanical parameters to plot", 
        ("Kinematics",),
#        index=None,
    )
    if category == "Kinematics":
        st.header(category, divider=True)
        st.subheader("Summary Grid")
        PlotLayout(st.session_state[m["dataset"]])
        st.write(m["top"])
        st.subheader("Interactive Plots")
        Plot(st.session_state[m["dataset"]])
        st.write(m["top"])

        report_bytes = Export.to_bytes(
            dataset=st.session_state[m["dataset"]],
            stats_map=st.session_state["add_to_rep"]
        )
        st.download_button(
            label="Download report.xlsx",
            data=report_bytes,
            file_name="report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
