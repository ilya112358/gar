import streamlit as st
from classes import DataSet, Plot

st.title("Measurement Two")
st.session_state["d2"] = DataSet("Archive/Data.2")
p2 = Plot(st.session_state["d2"])
st.markdown("[Go to the Top](#measurement-two)")
