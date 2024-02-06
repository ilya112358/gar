from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend, Range1d
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import toml

st.set_page_config(
    page_title="Gait Analysis Report", layout="wide"
)  # not a central column
st.image("GAR_topimage.jpg", width=512)


def process_data_file(file):
    """Load file, pre-process data, return dataframe"""

    df = pd.read_csv(file, sep="\t")
    # Now 'df' is a pandas DataFrame containing data from the file
    # Remove first 4 text rows (headers)
    df = df.drop(df.index[:4])
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.columns = df.columns.str.replace("Gait ", "")
    df.columns = df.columns.str.replace(".c3d", "")
    # The file's 1st col are numbers from 1 to 101
    df.rename(columns={df.columns[0]: "Gait cycle"}, inplace=True)
    df["Gait cycle"] -= 1
    # Add average over dynamic walks as the last column
    df1 = df.drop("Gait cycle", axis="columns")
    try:
        df1 = df1.drop("Static", axis="columns")
    except KeyError:  # ['Static.c3d'] not found (e.g., Moment)
        pass
    df["Mean"] = df1.mean(numeric_only=True, axis=1)
    return df


def plot_widegraph(bioparameter, dfs, colors, size, kind):
    """Visualize left and right"""

    def plot_df(df, lrb, kind):
        if kind == "kinematics":
            y_label = "Angle, degrees"
        else:
            y_label = "Force, N / Body Weight"
        p = figure(
            x_axis_label="Gait cycle, %",
            y_axis_label=y_label,
            height=size["height"],
            width=size["width"],
            tools="pan, box_zoom, reset",
            tooltips="[$name] @$name{0.00} at @{Gait cycle}%",  # [Mean] -0.77 at 33%
            toolbar_location="above",
            x_range=Range1d(start=0, end=100),  # Limit the x-axis, default (-5, 105)
        )
        p.border_fill_color = "seashell"
        p.xaxis.axis_label_text_font_style = p.yaxis.axis_label_text_font_style = (
            "normal"
        )
        p.xaxis.axis_label_text_font_size = p.yaxis.axis_label_text_font_size = "14px"
        lines, labels = [], []
        for col in range(1, len(df.columns)):
            column = df.columns[col]
            if column == "Static":
                color = colors["static"]
            elif "Mean" in column and lrb != "Both":
                color = colors["mean"]
            else:
                color = colors["color_list"][col - 1]
            if "Mean" in column:
                width = 3
            else:
                width = 1
            line = p.line(
                "Gait cycle",
                column,
                source=ColumnDataSource(df),
                color=color,
                width=width,
                name=column,
            )
            lines.append(line)
            labels.append((column, [line]))
        legend = Legend(items=labels)
        legend.border_line_color = "black"
        p.add_layout(legend, "right")
        components.html(
            file_html(
                p,
                "cdn",
            ),
            height=size["height"],
            width=size["width"],
        )

    st.header(bioparameter)
    opts = ["Left", "Right", "Both"]
    foot2plot = st.radio(
        f"Show plot for {bioparameter}", opts, horizontal=True, index=2
    )
    plot_df(dfs[opts.index(foot2plot)], foot2plot, kind)
    st.dataframe(dfs[3], hide_index=True)


# @st.cache_data
def load_config(file):
    """Load configuration file in a separate function to cache it but is it useful?"""

    with open(file, "r") as f:
        config = toml.load(f)
    return config


def process_dfs(file_pair):
    """Process data for left and right"""

    df_left = process_data_file(file_pair[1])
    df_right = process_data_file(file_pair[2])
    df_left.rename(columns={df_left.columns[-1]: "Left Mean"}, inplace=True)
    df_right.rename(columns={df_right.columns[-1]: "Right Mean"}, inplace=True)
    # combine Gait cycle and two Mean columns to plot both
    df_both = pd.concat(
        [df_left.iloc[:, :1], df_left.iloc[:, -1:], df_right.iloc[:, -1:]], axis=1
    )

    def stats(df, col):
        idxmax = df[col].idxmax()
        max = f"{df.loc[idxmax, col]:.2f} at {df.loc[idxmax, 'Gait cycle']}%"
        idxmin = df[col].idxmin()
        min = f"{df.loc[idxmin, col]:.2f} at {df.loc[idxmin, 'Gait cycle']}%"
        range = f"{df.loc[idxmax, col] - df.loc[idxmin, col]:.2f}"
        return max, min, range

    stats_left = stats(df_left, "Left Mean")
    stats_right = stats(df_right, "Right Mean")
    df_stats = pd.DataFrame(
        {
            "Side": ["Left", "Right"],
            "Maximum": [stats_left[0], stats_right[0]],
            "Minimum": [stats_left[1], stats_right[1]],
            "Range": [stats_left[2], stats_right[2]],
        }
    )
    return df_left, df_right, df_both, df_stats


def get_all_files(directory, data):
    """Get existing txt file pairs in a directory, return list of tuples"""

    file_pairs = []
    for item in data:
        left_file = os.path.join(directory, item["left_file"])
        right_file = os.path.join(directory, item["right_file"])
        if os.path.isfile(left_file) and os.path.isfile(right_file):
            file_pairs.append((item["name"], left_file, right_file))
    print(f"{len(file_pairs)} pairs loaded")
    return file_pairs


def select_dfs(config_files, uploaded_files):
    """Select uploaded files to process, return list of tuples"""

    file_pairs = []
    for item in config_files:
        left_file = [file for file in uploaded_files if file.name == item["left_file"]]
        right_file = [
            file for file in uploaded_files if file.name == item["right_file"]
        ]
        if left_file and right_file:
            file_pairs.append((item["name"], left_file[0], right_file[0]))
    print(f"{len(file_pairs)} pairs loaded")
    return file_pairs


directory = "Data"
config = load_config("config.toml")
if "data_kinematics" not in st.session_state:
    st.session_state.data_kinematics = []
if "data_kinetics" not in st.session_state:
    st.session_state.data_kinetics = []
if "dataset" not in st.session_state:
    st.session_state.dataset = False
st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D gets visualized")
st.write("---")

if not st.session_state.dataset:
    st.subheader("Upload your data or use example data.")
    with st.form("my-form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Import txt files exported from V3D and press submit",
            type="txt",
            accept_multiple_files=True,
        )
        submitted = st.form_submit_button("submit")
    data_kinematics, data_kinetics = [], []
    if submitted:
        data_kinematics = select_dfs(config["kinematics"], uploaded_files)
        data_kinetics = select_dfs(config["kinetics"], uploaded_files)
    elif st.button("Press to use example data"):
        data_kinematics = get_all_files(directory, config["kinematics"])
        data_kinetics = get_all_files(directory, config["kinetics"])
    if data_kinematics or data_kinetics:
        for file_pair in data_kinematics:
            st.session_state.data_kinematics.append(
                (file_pair[0], process_dfs(file_pair))
            )
        for file_pair in data_kinetics:
            st.session_state.data_kinetics.append(
                (file_pair[0], process_dfs(file_pair))
            )
        st.session_state.dataset = True
        st.rerun()

with st.sidebar:
    st.markdown("[Go to the Top](#gait-analysis-report)")
    st.subheader("Parameters:")
st.sidebar.write("Kinematics:")
for file_pair in st.session_state.data_kinematics:
    plot_widegraph(
        file_pair[0], file_pair[1], config["colors"], config["size"], "kinematics"
    )
    section = file_pair[0]
    lnk = section.lower().replace(" ", "-").replace("_", "-")  # slugify
    st.sidebar.markdown(f"[{section}](#{lnk})")
st.sidebar.write("Kinetics:")
for file_pair in st.session_state.data_kinetics:
    plot_widegraph(
        file_pair[0], file_pair[1], config["colors"], config["size"], "kinetics"
    )
    section = file_pair[0]
    lnk = section.lower().replace(" ", "-").replace("_", "-")  # slugify
    st.sidebar.markdown(f"[{section}](#{lnk})")
