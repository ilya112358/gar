import streamlit as st

from classes import Plot

params1 = [item[0] for item in st.session_state["d1"].data2plot]
params2 = [item[0] for item in st.session_state["d2"].data2plot]
params = []
for item in params1:
    if item in params2:
        params.append(item)
st.title("Comparison")
st.write("Select a parameter to compare")
param = st.selectbox("Select parameter", params)
p1 = Plot(st.session_state["d1"], param, src="from measurement_one")
p2 = Plot(st.session_state["d2"], param, src="from measurement_two")
