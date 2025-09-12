import streamlit as st
import pandas as pd
import zipfile
import importlib
import classes
importlib.reload(classes)  # reload config
from classes import DataSet, Plot, PlotLayout, Export, DataCompare, PlotCompare

NUM_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten"
}

def home():
    st.session_state["current_page"] = 0
    st.image("GAR_topimage.jpg", width=512)
    st.title("Gait Analysis Report")
    st.text("where the data from Visual3D gets visualized")
    st.write("This is the multi-page web dashboard")
    st.write("👈 Use the sidebar to navigate between pages")
    st.write("- Press **Add Measurement** to load and visualize data from the dataset (up to 7 measurements)")
    st.write("- Choose **Compare** to compare any two loaded measurements")
    st.write("- Choose **Home** and reload the page in the browser to start again")
    st.write("⬆️ Upload data exported from Visual3D or use example data for demonstration")
    st.write("📊 The following data is processed:")
    st.write("- Subject metadata")
    st.write("- Temporal and Spatial parameters")
    st.write("- Gait Profile Score")
    st.write("- Kinematics")
    st.write("⏱ For the moment, the comparison page functionality is limited")
    st.write("Write your reactions to ilya112358@gmail.com or visit GitHub repo https://github.com/ilya112358/gar")
    st.write("*(version 2025.08)*")

def measurement(m):
    st.header(m["title"])
    # if page changed (incl from Home)
    if st.session_state["current_page"] != m["page"]:
        st.session_state["current_page"] = m["page"]
    if m["dataset"] not in st.session_state:
        uploaded_file = None
        col1, col2 = st.columns(2, vertical_alignment="center")
        with col1:
            uploaded_file = st.file_uploader("Upload a zip file", type=["zip"], key="upload")
        with col2:
            if uploaded_file is None and m["page"] in (1, 2):
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
            st.write(m["link_top"])

            @st.fragment
            def individual_plot():
                st.subheader("Interactive Plots")
                Plot(m["dataset"])  # "d1"
                st.write(m["link_top"])

                def get_export_data(dataset_key):
                    """Aggregate export data from all plot states for a dataset"""
                    plot_config_key = f"{dataset_key}_Plot"
                    
                    if plot_config_key in st.session_state.get("plot_configs", {}):
                        plot_state = st.session_state["plot_configs"][plot_config_key]
                        return plot_state.get("add_to_rep", {})
                    return {}

                report_bytes = Export.to_bytes(
                    dataset=st.session_state[m["dataset"]],
                    stats_map=get_export_data(m["dataset"])
                )                
                st.download_button(
                    label="Download report.xlsx",
                    data=report_bytes,
                    file_name="report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            individual_plot()
        elif category == "Kinetics":
            st.header(category, divider=True)
            st.subheader("Summary Grid")
            PlotLayout(st.session_state[m["dataset"]], "kinetics")
            st.write(m["link_top"])
        else:
            st.subheader("🚧👷‍♂️ Under construction!")

def make_measurement_metadata(num: int) -> dict:
    word = NUM_WORDS[num]          # lowercase version
    word_cap = word.title()        # capitalized for title
    return {
        "title": f"Measurement {word_cap}",
        "url_path": f"measurement-{word}",
        "dataset": f"d{num}",
        "archive": f"Examples/Data{num}.zip",
        "page": num,
        "link_top": f"[Go to the Top](#measurement-{word})"
    }    

def make_measurement_page(m: dict):
    # Return a zero-arg callable
    def _page():
        measurement(m)
    return _page

def comparison():
    st.title("Comparison")
    st.markdown("Pick any **two** loaded measurements to compare.")

    # Build a dict: {title: dataset_key} for loaded measurements
    loaded = {
        m["title"]: m["dataset"]
        for m in st.session_state.get("pages", [])
        if m["dataset"] in st.session_state
    }
    if len(loaded) < 2:
        st.error("Please load at least two measurements first!", icon="🚨")
        st.stop()
    chosen_titles = st.multiselect(
        "Choose two measurements",
        options=list(loaded.keys()),
        default=list(loaded.keys())[:2],
        max_selections=2
    )
    if len(chosen_titles) != 2:
        st.info("Select exactly two measurements to proceed.")
        st.stop()
    key_a, key_b = loaded[chosen_titles[0]], loaded[chosen_titles[1]]
    ds_a, ds_b = st.session_state[key_a], st.session_state[key_b]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {chosen_titles[0]}")
        st.dataframe(ds_a.info, hide_index=True)
    with col2:
        st.markdown(f"### {chosen_titles[1]}")
        st.dataframe(ds_b.info, hide_index=True)

    st.markdown("You can only compare parameters present in **both** measurements.")
    st.markdown("Graphs are **solid** for the first measurement and **dashed** for the second.")
    dc = DataCompare(ds_a, ds_b)
    param = st.selectbox("Select parameter", list(dc.data2plot.keys()))
    PlotCompare(dc, param)

# Initialization
st.set_page_config(
    page_title="Gait Analysis Report", layout="wide"    # not a central column
)
if "plot_configs" not in st.session_state:
    st.session_state["plot_configs"] = {}   # for plot persistence
if "pages" not in st.session_state:
    st.session_state.pages = []  # list of autogenerated page titles
pages = [st.Page(home, title="Home", icon=":material/home:"), ] # list of actual streamlit Page objects
if st.sidebar.button("Add Measurement"):    # TODO gray-out when limit reached
    idx = len(st.session_state.pages)
    if idx < 7:
        m = make_measurement_metadata(idx+1)
        st.session_state.pages.append(m)
for idx, m in enumerate(st.session_state.pages):
    pages.append(st.Page(make_measurement_page(m), title=m["title"], icon=":material/analytics:", url_path=m["url_path"]))
pages.append(st.Page(comparison, title="Compare", icon=":material/balance:"))
current = st.navigation(pages)
current.run()
