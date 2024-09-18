import pandas as pd
import streamlit as st
import zipfile
from classes import DataSet, Plot, PlotLayout

uploaded_file = None
col1, col2 = st.columns(2, vertical_alignment="center")
with col1:
    uploaded_file = st.file_uploader("Upload a zip file", type=["zip"], key="upload")
with col2:
    if uploaded_file is None:
        if st.button("Or use example data"):
            uploaded_file = "Archive/Data1.zip"
if uploaded_file is not None:
    with zipfile.ZipFile(uploaded_file) as zf:
        # make a dict where zf.namelist() will be the keys and the values will be dfs read from the files
        d = {x: pd.read_csv(zf.open(x), sep="\t") for x in zf.namelist()}
        st.session_state["d1"] = DataSet(d)

if "d1" in st.session_state:
    st.title(
        f"{st.session_state['d1'].info['First Name']} {st.session_state['d1'].info['Last Name']}, "
        f"{st.session_state['d1'].info['Creation date']}, "
        f"{st.session_state['d1'].info['Test condition']}"
    )
else:
    st.title("Measurement One")
    
if "d1" in st.session_state:
    if st.session_state["current_page"] != 1:
        st.session_state["current_page"] = 1
        st.session_state["reset_stats"] = True
    st.markdown("## Metadata")
    st.dataframe(st.session_state["d1"].info)
    st.markdown("## Temporal and Spatial data")
    st.dataframe(st.session_state["d1"].ts)
    st.markdown("## Summary Grid")
    PlotLayout(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
    st.markdown("## Individual Plots")
    Plot(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
