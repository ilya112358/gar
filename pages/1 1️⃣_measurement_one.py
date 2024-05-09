import streamlit as st
from classes import DataSet, Plot, PlotLayout

st.title("Measurement One")
if st.button("Press to use example data"):
    st.session_state["d1"] = DataSet("Archive/Data.1")
if "d1" in st.session_state:
    st.markdown("## Metadata")
    st.dataframe(st.session_state["d1"].info)
    st.markdown("## Summary Grid")
    PlotLayout(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
    st.markdown("## Individual Plots")
    Plot(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
