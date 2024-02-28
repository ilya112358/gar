
import streamlit as st
from classes import DataSet, Plot, PlotLayout

st.title("Measurement Two")
if st.button("Press to use example data"):
    st.session_state["d2"] = DataSet("Archive/Data.2")
if "d2" in st.session_state:
    st.text(st.session_state["d2"].info)
    st.markdown("## Summary Grid")
    st.markdown("All graphs show mean values, :red[red for Left] and :blue[blue for Right]")
    st.markdown("Check [individual plots](#individual-plots) to see consistency and relevant statistics")
    PlotLayout(st.session_state["d2"])
    st.markdown("[Go to the Top](#measurement-two)")
    st.markdown("## Individual Plots")
    Plot(st.session_state["d2"])
    st.markdown("[Go to the Top](#measurement-two)")