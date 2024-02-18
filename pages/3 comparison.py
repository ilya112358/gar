import streamlit as st

from classes import DataCompare, PlotCompare

if "d1" not in st.session_state or "d2" not in st.session_state:
    st.error("Please load both measurements first!", icon="🚨")
    st.stop()
dc = DataCompare(st.session_state["d1"], st.session_state["d2"])
st.title("Comparison")
st.markdown("This page allows you to compare the two measurements.")
param = st.selectbox("Select parameter", list(dc.data2plot.keys()))
pc = PlotCompare(dc, param)
st.markdown("[Go to the Top](#comparison)")