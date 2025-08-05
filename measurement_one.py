import pandas as pd
import streamlit as st
import zipfile
from classes import DataSet, Plot, PlotLayout, Export

m = {
    "title": "Measurement One",
    "dataset": "d1",
    "archive": "Examples/Data1.zip",
    "page": 1,
    "top": "[Go to the Top](#measurement-one)"
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
            # all file paths (skip folders)
            all_members = [m for m in zf.namelist() if not m.endswith('/')]
            # if there's an Export/ folder, use only its contents
            if any(m.startswith('Export/') for m in all_members):
                members = [m for m in all_members if m.startswith('Export/')]
            else:
                members = all_members
            # read each TSV into a DataFrame, keyed by its filename
            data_dict = {
                path.rsplit('/', 1)[-1]: pd.read_csv(zf.open(path), sep='\t')
                for path in members
            }
            st.session_state[m["dataset"]] = DataSet(data_dict)
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
    st.header("Gait Profile Score", divider=True)
    st.subheader(f"Overall GPS: {st.session_state[m["dataset"]].gps[0]}")
    st.dataframe(st.session_state[m["dataset"]].gps[1], hide_index=True)
    category = st.selectbox(
        "You can choose the category of biomechanical parameters to plot", 
        ("Kinematics", "Kinetics", "EMG"),
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
    else:
        st.subheader("🚧👷‍♂️ Under construction!")
