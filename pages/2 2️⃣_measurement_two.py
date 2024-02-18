import streamlit as st
from classes import DataSet, Plot

st.title("Measurement Two")
if st.button("Press to use example data"):
    st.session_state["d2"] = DataSet("Archive/Data.2")
if "d2" in st.session_state:
    st.text(st.session_state["d2"].info)
    Plot(st.session_state["d2"])
    st.markdown("[Go to the Top](#measurement-two)")
