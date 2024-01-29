from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend, Range1d
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import toml

st.set_page_config(layout="wide")  # not a central column


@st.cache_data
def process_data_file(directory, file):
    """Load file, pre-process data, return dataframe"""

    file_path = os.path.join(directory, file)
    df = pd.read_csv(file_path, sep="\t")
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


@st.cache_data
def process_pair(directory, files):
    """Process data for left and right"""

    df_left = process_data_file(directory, files[1])
    df_right = process_data_file(directory, files[2])
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


def plot_widegraph(bioparameter, dfs, colors, size):
    """Visualize left and right"""

    def plot_df(df, lrb):
        p = figure(
            x_axis_label="Gait cycle, %",
            y_axis_label="Degrees",
            height=size["height"],
            width=size["width"],
            tools="pan, box_zoom, reset",
            tooltips="[$name] @$name{0.00} at @{Gait cycle}",  # [Mean] -0.77 at 33
            toolbar_location="above",
            x_range=Range1d(start=0, end=100),  # Limit the x-axis, default (-5, 105)
        )
        p.border_fill_color = "seashell"
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
    plot_df(dfs[opts.index(foot2plot)], foot2plot)
    st.dataframe(dfs[3], hide_index=True)


@st.cache_data
def get_all_files(directory, data):
    """Get existing txt file pairs in a directory, return list of tuples"""

    file_pairs = []
    for item in data:
        if os.path.isfile(
            os.path.join(directory, item["left_file"])
        ) and os.path.isfile(os.path.join(directory, item["right_file"])):
            file_pairs.append((item["name"], item["left_file"], item["right_file"]))
    print(f"{len(file_pairs)} pairs loaded")
    return file_pairs


@st.cache_data
def load_config(file):
    """Load configuration file in a separate function to cache it"""

    with open(file, "r") as f:
        config = toml.load(f)
    return config


directory = "Data"
config = load_config("config.toml")
data_files = get_all_files(directory, config["data"])

st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D gets visualized")

with st.sidebar:
    st.markdown("[Go to the Top](#gait-analysis-report)")
    st.subheader("Sections list")
    for f in data_files:
        section = f[0]
        lnk = section.lower().replace(" ", "-").replace("_", "-")  # slugify
        st.markdown(f"[{section}](#{lnk})")
    if st.button("Clear Cache"):
        st.cache_data.clear()

for file in data_files:
    dfs = process_pair(directory, file)
    plot_widegraph(file[0], dfs, config["colors"], config["size"])
