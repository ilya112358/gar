import streamlit as st
from classes import DataSet, Plot, PlotLayout

if st.button("Press to use example data"):
    st.session_state["d1"] = DataSet("Archive/Data.1")

if "d1" in st.session_state:
    st.title(
        f"{st.session_state['d1'].info['First Name']} {st.session_state['d1'].info['Last Name']}, "
        f"{st.session_state['d1'].info['Creation date']}, "
        f"{st.session_state['d1'].info['Test condition']}"
    )
else:
    st.title("Measurement One")
    
if "d1" in st.session_state:
    if st.session_state["current_page"] != 1:
        st.session_state["current_page"] = 1
        st.session_state["reset_stats"] = True
    st.markdown("## Metadata")
    st.dataframe(st.session_state["d1"].info)
    st.markdown("## Temporal and Spatial data")
    st.dataframe(st.session_state["d1"].ts)
    st.markdown("## Summary Grid")
    PlotLayout(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
    st.markdown("## Individual Plots")
    Plot(st.session_state["d1"])
    st.markdown("[Go to the Top](#measurement-one)")
