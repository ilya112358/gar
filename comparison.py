import streamlit as st

from classes import DataCompare, PlotCompare

if "d1" not in st.session_state or "d2" not in st.session_state:
    st.error("Please load both measurements first!", icon="🚨")
    st.stop()

st.title("Comparison")
st.markdown("This page allows you to compare the two measurements.")
st.markdown("## Measurement 1:")
st.dataframe(st.session_state["d1"].info)
st.markdown("## Measurement 2:")
st.dataframe(st.session_state["d2"].info)
st.markdown("You can compare parameters present in both measurements.")
st.markdown("Graphs are solid lines for the first measurement and dashed lines for the second.")
dc = DataCompare(st.session_state["d1"], st.session_state["d2"])
param = st.selectbox("Select parameter", list(dc.data2plot.keys()))
pc = PlotCompare(dc, param)
