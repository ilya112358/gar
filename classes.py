from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Legend, Range1d

import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import toml


class Config:
    __file = "config.toml"

    def __init__(self):
        with open(self.__file, "r") as f:
            self.__config = toml.load(f)
        self.kinematics = self.__config["kinematics"]
        self.colors = self.__config["colors"]
        self.size = self.__config["size"]


c = Config()


class DataSet:
    """
    A class used to represent a DataSet for processing and plotting.

    Attributes
    ----------
    data2plot : dict
        a dictionary to store processed data for plotting

    Methods
    -------
    process_dfs(file_pair):
        Process data for left and right, add stats, return 4 dataframes.
    process_data_file(file):
        Load file, pre-process data, return a dataframe.
    """

    def __init__(self, directory):
        file_pairs = []
        self.data2plot = {}
        with open(os.path.join(directory, "Info.txt"), "r") as f:
            self.info = f.read()
        for item in c.kinematics:
            left_file = os.path.join(directory, item["left_file"])
            right_file = os.path.join(directory, item["right_file"])
            if os.path.isfile(left_file) and os.path.isfile(right_file):
                file_pairs.append((item["name"], left_file, right_file))
        for file_pair in file_pairs:
            self.data2plot[file_pair[0]] = self.process_dfs(file_pair)
        print(f"{len(self.data2plot)} pairs loaded")

    def process_dfs(self, file_pair):
        df_left = self.process_data_file(file_pair[1])
        df_right = self.process_data_file(file_pair[2])
        df_left.rename(columns={df_left.columns[-1]: "Left Mean"}, inplace=True)
        df_right.rename(columns={df_right.columns[-1]: "Right Mean"}, inplace=True)
        # combine Gait cycle and two Mean columns to plot both
        df_both = pd.concat(
            [df_left.iloc[:, :1], df_left.iloc[:, -1:], df_right.iloc[:, -1:]],
            axis=1,
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

    def process_data_file(self, file):
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


class DataCompare:
    """
    A class used to compare two datasets.

    Attributes
    ----------
    data2plot : dict
        A dictionary where the keys are the names of the data sets and the values are tuples.
        Each tuple contains two dataframes: the first dataframe contains the "Left Mean" and "Right Mean"
        values from both datasets, and the second dataframe contains the "Maximum", "Minimum", and "Range"
        values from both datasets.
    """

    def __init__(self, d1, d2):
        self.data2plot = {}
        for item in d1.data2plot:
            if item in d2.data2plot:
                d_df_both = d1.data2plot[item][2].copy()
                d2_df_both = d2.data2plot[item][2]
                d_df_stats = d1.data2plot[item][3].copy()
                d2_df_stats = d2.data2plot[item][3]
                # connect d1_df_both and d2_df_both
                # rename columns to avoid duplicates
                d_df_both.rename(
                    columns={"Left Mean": "Left Mean 1", "Right Mean": "Right Mean 1"},
                    inplace=True,
                )
                d_df_both["Left Mean 2"] = d2_df_both["Left Mean"]
                d_df_both["Right Mean 2"] = d2_df_both["Right Mean"]
                # connect d1_df_stats and d2_df_stats
                # rename columns to avoid duplicates
                d_df_stats.rename(
                    columns={
                        "Maximum": "Maximum 1",
                        "Minimum": "Minimum 1",
                        "Range": "Range 1",
                    },
                    inplace=True,
                )
                d_df_stats["Maximum 2"] = d2_df_stats["Maximum"]
                d_df_stats["Minimum 2"] = d2_df_stats["Minimum"]
                d_df_stats["Range 2"] = d2_df_stats["Range"]
                self.data2plot[item] = (d_df_both, d_df_stats)


class Figure:
    """
    A class used to represent a Figure for plotting.

    Attributes
    ----------
    figure : bokeh.plotting.figure
        a figure object with various default attributes

    Methods
    -------
    add_line(df, column, color, width, line_dash="solid"):
        Adds a line to the figure.
    add_legend(labels):
        Adds a legend to the figure.
    render():
        Renders the figure as an HTML component.
    """

    def __init__(self, x_label="Gait cycle, %", y_label="Angle, degrees"):
        self.figure = figure(
            x_axis_label=x_label,
            y_axis_label=y_label,
            height=c.size["height"],
            width=c.size["width"],
            tools="pan, box_zoom, reset",
            # will {Gait cycle} work for GRF?
            tooltips="[$name] @$name{0.00} at @{Gait cycle}%",  # [Mean] -0.77 at 33%
            toolbar_location="above",
            x_range=Range1d(start=0, end=100),  # Limit the x-axis, default (-5, 105)
        )
        self.figure.border_fill_color = "seashell"
        self.figure.xaxis.axis_label_text_font_style = "normal"
        self.figure.yaxis.axis_label_text_font_style = "normal"
        self.figure.xaxis.axis_label_text_font_size = "14px"
        self.figure.yaxis.axis_label_text_font_size = "14px"
        self.figure.toolbar.logo = None

    def add_line(self, df, column, color, width, line_dash="solid"):
        line = self.figure.line(
            "Gait cycle",
            column,
            source=ColumnDataSource(df),
            color=color,
            width=width,
            name=column,
            line_dash=line_dash,
        )
        return line

    def add_legend(self, labels):
        legend = Legend(items=labels)
        legend.border_line_color = "black"
        self.figure.add_layout(legend, "right")

    def render(self):
        components.html(
            file_html(
                self.figure,
                "cdn",
            ),
            height=c.size["height"],
            width=c.size["width"],
        )


class Plot:
    """Plot the data from the DataSet object"""

    def __init__(self, d):
        params = list(d.data2plot.keys())
        self.params2plot = st.multiselect(
            "You can choose multiple parameters to plot", params
        )
        for param in self.params2plot:
            self.plot(param, d.data2plot[param])

    def plot(self, bioparameter, dfs):
        st.header(f"{bioparameter}")
        opts = ["Left", "Right", "Both"]
        foot2plot = st.radio(
            f"Show plot for {bioparameter}", opts, horizontal=True, index=2
        )
        fig = Figure()
        labels = []
        df = dfs[opts.index(foot2plot)]
        for col in range(1, len(df.columns)):
            column = df.columns[col]
            if column == "Static":
                color = c.colors["static"]
            elif "Mean" in column and foot2plot != "Both":
                color = c.colors["mean"]
            else:
                color = c.colors["color_list"][col - 1]
            width = 3 if "Mean" in column else 1
            line = fig.add_line(df, column, color, width)
            labels.append((column, [line]))
        fig.add_legend(labels)
        fig.render()
        st.markdown("###### Mean value statistics")
        st.dataframe(dfs[3], hide_index=True)


class PlotCompare:
    """Plot the comparison of the two datasets"""

    def __init__(self, dc, param):
        self.plot_compare(dc.data2plot[param][0], dc.data2plot[param][1], param)

    def plot_compare(self, df_both, df_stats, param):
        st.header(f"{param}")
        st.dataframe(df_stats, hide_index=True)
        fig = Figure()
        labels = []
        for col in range(1, len(df_both.columns)):
            column = df_both.columns[col]
            line_dash = "solid" if "Mean 1" in column else "dashed"
            color = "blue" if "Left" in column else "red"
            line = fig.add_line(df_both, column, color, width=2, line_dash=line_dash)
            labels.append((column, [line]))
        fig.add_legend(labels)
        fig.render()
