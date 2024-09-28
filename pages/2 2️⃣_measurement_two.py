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
            uploaded_file = "Archive/Data2.zip"
if uploaded_file is not None:
    with zipfile.ZipFile(uploaded_file) as zf:
        # make a dict where zf.namelist() will be the keys and the values will be dfs read from the files
        d = {x: pd.read_csv(zf.open(x), sep="\t") for x in zf.namelist()}
        st.session_state["d2"] = DataSet(d)

if "d2" in st.session_state:
    title = (
        f"{st.session_state["d2"].info['First Name']} {st.session_state["d2"].info['Last Name']}, "
        f"{st.session_state["d2"].info['Creation date']}, "
        f"{st.session_state["d2"].info['Test condition']}"
    )
    st.title(f"{title}")
else:
    st.title("Load Measurement")
    st.write("Please upload a zip file with measurement data or use example data. Choose above.")

if "d2" in st.session_state:
    # page changed
    if st.session_state["current_page"] != 2:
        st.session_state["current_page"] = 2
        st.session_state["reset_stats"] = True
        if "add_to_rep" in st.session_state:
            del st.session_state["add_to_rep"]
    # page layout
    st.header("Subject", divider=True)
    st.dataframe(st.session_state["d2"].info)
    st.header("Temporal and Spatial", divider=True)
    st.dataframe(st.session_state["d2"].ts)
    st.header("Summary Grid", divider=True)
    PlotLayout(st.session_state["d2"])
    st.write("[Go to the Top](#load-measurement)")
    st.header("Individual Plots", divider=True)
    Plot(st.session_state["d2"])
    st.write("[Go to the Top](#load-measurement)")
    
    # Write df in Excel format to memory and link to Download button
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet()  # writer.sheets['Sheet1']
    # add title
    bold = workbook.add_format({'bold': True})  # formatter
    worksheet.write_string(0, 0, title, bold)
    row_num = 2
    # subject info
    info = pd.DataFrame.from_dict(st.session_state["d2"].info, orient="index")
    info.rename(columns={info.columns[0]: 'Subject'}, inplace=True)
    info.to_excel(writer, sheet_name='Sheet1', startrow=row_num)
    row_num += info.shape[0] + 2
    # temporal and spatial
    ts = pd.DataFrame.from_dict(st.session_state["d2"].ts, orient="index")
    ts.rename(columns={ts.columns[0]: 'Temporal and Spatial'}, inplace=True)
    ts.to_excel(writer, sheet_name='Sheet1', startrow=row_num)
    row_num += ts.shape[0] + 2
    # format column width
    longest_string_length = max(max(len(str(i)) for i in ts.index), max(len(str(i)) for i in info.index))
    worksheet.set_column(0, 0, longest_string_length)
    # add individual stats
    for param2plot, stats in st.session_state["add_to_rep"].items():
        worksheet.write_string(row_num, 0, param2plot, bold)
        row_num += 1
        stats["df_stats"].to_excel(writer, sheet_name='Sheet1', index=False, startrow=row_num)
        row_num += len(stats["df_stats"]) + 2
        worksheet.write_string(row_num, 0, stats["analysis"])
        row_num += 2
    # save
    writer.close()
    st.download_button(
        label="Download report.xlsx",
        data=output.getvalue(),
        file_name="report.xlsx",
        mime="application/vnd.ms-excel"
    )
    