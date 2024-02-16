import streamlit as st
from classes import c, DataSet

d = DataSet("Data", c.kinematics)
st.write(d.data2plot)