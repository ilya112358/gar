import streamlit as st
from classes import c, DataSet, Plot

st.title("Measurement One")
d1 = DataSet("Data")
p1 = Plot(d1)
st.markdown("[Go to the Top](#measurement-one)")
