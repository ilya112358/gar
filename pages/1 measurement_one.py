import streamlit as st
from classes import DataSet, Plot

st.title("Measurement One")
st.session_state["d1"] = DataSet("Archive/Data.1")
p1 = Plot(st.session_state["d1"])
st.markdown("[Go to the Top](#measurement-one)")
