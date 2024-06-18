import streamlit as st
from classes import DataSet, Plot, PlotLayout

st.title("Measurement Two")
if st.button("Press to use example data"):
    st.session_state["d2"] = DataSet("Archive/Data.2")
if "d2" in st.session_state:
    if st.session_state["current_page"] != 2:
        st.session_state["current_page"] = 2
        st.session_state["reset_stats"] = True
    st.markdown("## Metadata")
    st.dataframe(st.session_state["d2"].info)
    st.markdown("## Summary Grid")
    PlotLayout(st.session_state["d2"])
    st.markdown("[Go to the Top](#measurement-two)")
    st.markdown("## Individual Plots")
    Plot(st.session_state["d2"])
    st.markdown("[Go to the Top](#measurement-two)")
    