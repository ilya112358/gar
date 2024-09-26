from io import BytesIO
import pandas as pd
import streamlit as st
import zipfile
from classes import DataSet, Plot, PlotLayout

uploaded_file = None
col1, col2 = st.columns(2, vertical_alignment="center")
with col1:
    uploaded_file = st.file_uploader("Upload a zip file", type=["zip"], key="upload")
with col2:
    if uploaded_file is None:
        if st.button("Or use example data"):
            uploaded_file = "Archive/Data1.zip"
if uploaded_file is not None:
    with zipfile.ZipFile(uploaded_file) as zf:
        # make a dict where zf.namelist() will be the keys and the values will be dfs read from the files
        d = {x: pd.read_csv(zf.open(x), sep="\t") for x in zf.namelist()}
        st.session_state["d1"] = DataSet(d)

if "d1" in st.session_state:
    title = (
        f"{st.session_state['d1'].info['First Name']} {st.session_state['d1'].info['Last Name']}, "
        f"{st.session_state['d1'].info['Creation date']}, "
        f"{st.session_state['d1'].info['Test condition']}"
    )
    st.title(f"{title}")
else:
    st.title("Measurement One")

if "d1" in st.session_state:
    if st.session_state["current_page"] != 1:
        st.session_state["current_page"] = 1
        st.session_state["reset_stats"] = True
    st.header("Metadata", divider=True)
    st.dataframe(st.session_state["d1"].info)
    st.header("Temporal and Spatial", divider=True)
    st.dataframe(st.session_state["d1"].ts)
    st.header("Summary Grid", divider=True)
    PlotLayout(st.session_state["d1"])
    st.write("[Go to the Top](#measurement-one)")
    st.header("Individual Plots", divider=True)
    Plot(st.session_state["d1"])
    st.write("[Go to the Top](#measurement-one)")
    
    # Write df in Excel format to memory and link to Download button
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet()  # writer.sheets['Sheet1']
    # add title
    bold = workbook.add_format({'bold': True})  # formatter
    worksheet.write_string(0, 0, title, bold)
    info = pd.DataFrame.from_dict(st.session_state["d1"].info, orient="index")
    info.rename(columns={info.columns[0]: 'Metadata'}, inplace=True)
    info.to_excel(writer, sheet_name='Sheet1', startrow=2)
    ts = pd.DataFrame.from_dict(st.session_state["d1"].ts, orient="index")
    ts.rename(columns={ts.columns[0]: 'Temporal and Spatial'}, inplace=True)
    ts.to_excel(writer, sheet_name='Sheet1', startrow=2+info.shape[0]+2)
    longest_string_length = max(max(len(str(i)) for i in ts.index), max(len(str(i)) for i in info.index))
    worksheet.set_column(0, 0, longest_string_length)
    writer.close()
    st.download_button(
        label="Download stats.xlsx",
        data=output.getvalue(),
        file_name="stats.xlsx",
        mime="application/vnd.ms-excel"
    )
