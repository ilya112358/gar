import pandas as pd
import streamlit as st
import zipfile
from classes import DataSet, Plot, PlotLayout, Export

st.title("measurement two")
uploaded_file = None
col1, col2 = st.columns(2, vertical_alignment="center")
with col1:
    uploaded_file = st.file_uploader("Upload a zip file", type=["zip"], key="upload")
with col2:
    if uploaded_file is None:
        if st.button("Or use example data"):
            uploaded_file = "Archive/Data2.zip"
if uploaded_file is not None:
    with zipfile.ZipFile(uploaded_file) as zf:
        # make a dict where zf.namelist() will be the keys and the values will be dfs read from the files
        d = {x: pd.read_csv(zf.open(x), sep="\t") for x in zf.namelist()}
        st.session_state["d2"] = DataSet(d)

if "d2" in st.session_state:
    title = (
        f"{st.session_state["d2"].info['First Name']} {st.session_state["d2"].info['Last Name']}, "
        f"{st.session_state["d2"].info['Creation date']}, "
        f"{st.session_state["d2"].info['Test condition']}"
    )
    st.title(f"{title}")
else:
    st.subheader("Load Measurement")
    st.write("Please upload a zip file with measurement data or use example data. Choose above.")

if "d2" in st.session_state:
    # page changed
    if st.session_state["current_page"] != 2:
        st.session_state["current_page"] = 2
        st.session_state["reset_stats"] = True
        if "add_to_rep" in st.session_state:
            del st.session_state["add_to_rep"]
    # page layout
    st.header("Subject", divider=True)
    # convert to dataframe
    info_df = pd.DataFrame(st.session_state["d2"].info.items(), columns=['Metadata', 'Value'])
    st.dataframe(info_df, hide_index=True)
    st.header("Temporal and Spatial", divider=True)
    # st.dataframe(st.session_state["d2"].ts.fillna(''), hide_index=True)  # removing None (np.nan) leads to a warning due to mixed types
    st.dataframe(st.session_state["d2"].ts, hide_index=True)
    category = st.selectbox(
        "You can choose the category of biomechanical parameters to plot", 
        ("Kinematics",),
#        index=None,
    )
    if category == "Kinematics":
        st.header(category, divider=True)
        st.subheader("Summary Grid")
        PlotLayout(st.session_state["d2"])
        st.write("[Go to the Top](#measurement-one)")

        st.subheader("Interactive Plots")
        Plot(st.session_state["d2"])
        st.write("[Go to the Top](#measurement-one)")

        # Single call to produce report bytes
        report_bytes = Export.to_bytes(
            title=title,
            info_df=info_df,
            data_obj=st.session_state["d2"],
            stats_map=st.session_state["add_to_rep"]
        )

        st.download_button(
            label="Download report.xlsx",
            data=report_bytes,
            file_name="report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
