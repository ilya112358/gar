import streamlit as st
from classes import c, DataSet, Plot

st.title("Measurement Two")
d2 = DataSet("Data")
p2 = Plot(d2)
st.markdown("[Go to the Top](#measurement-two)")
