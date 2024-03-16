import streamlit as st
from classes import DataSet, Plot, PlotLayout

st.title("Measurement One")
if st.button("Press to use example data"):
    st.session_state["d1"] = DataSet("Archive/Data.1")
if "d1" in st.session_state:
    st.text(st.session_state["d1"].info)
    st.markdown("## Summary Grid")
    st.markdown("All graphs show mean values, :red[red for Left] and :blue[blue for Right]")
    st.markdown("Check [inividual plots](#individual-plots) to see consistency and relevant statistics")
    PlotLayout(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
    st.markdown("## Individual Plots")
    Plot(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
