import streamlit as st
import pandas as pd
import zipfile
import importlib
import classes
importlib.reload(classes)  # reload config
from classes import DataSet, Plot, PlotLayout, Export, DataCompare, PlotCompare

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

def measurement(m):
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

def measurement_one():
    m = {
        "title": "Measurement One",
        "dataset": "d1",
        "archive": "Examples/Data1.zip",
        "page": 1,
        "top": "[Go to the Top](#measurement-one)"
    }
    measurement(m)

def measurement_two():
    m = {
        "title": "Measurement Two",
        "dataset": "d2",
        "archive": "Examples/Data2.zip",
        "page": 2,
        "top": "[Go to the Top](#measurement-two)"
    }
    measurement(m)

def comparison():
    if "d1" not in st.session_state or "d2" not in st.session_state:
        st.error("Please load both measurements first!", icon="🚨")
        st.stop()

    st.title("Comparison")
    st.markdown("This page allows you to compare the two measurements.")
    st.markdown("## Measurement One:")
    st.dataframe(st.session_state["d1"].info)
    st.markdown("## Measurement Two:")
    st.dataframe(st.session_state["d2"].info)
    st.markdown("You can compare parameters present in both measurements.")
    st.markdown("Graphs are solid lines for the first measurement and dashed lines for the second.")
    dc = DataCompare(st.session_state["d1"], st.session_state["d2"])
    param = st.selectbox("Select parameter", list(dc.data2plot.keys()))
    pc = PlotCompare(dc, param)

page_home = st.Page(home, title="Home", icon=":material/home:")
page1 = st.Page(measurement_one, title="Measurement One", icon=":material/counter_1:")
page2 = st.Page(measurement_two, title="Measurement Two", icon=":material/counter_2:")
page3 = st.Page(comparison, title="Compare", icon=":material/balance:")
current = st.navigation([page_home, page1, page2, page3])
current.run()
