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
    def __init__(self, directory):
        file_pairs = []
        self.data2plot = []
        with open(os.path.join(directory, "Info.txt"), "r") as f:
            self.info = f.read()
        for item in c.kinematics:
            left_file = os.path.join(directory, item["left_file"])
            right_file = os.path.join(directory, item["right_file"])
            if os.path.isfile(left_file) and os.path.isfile(right_file):
                file_pairs.append((item["name"], left_file, right_file))

        def process_dfs(file_pair):
            """Process data for left and right"""

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

            df_left = process_data_file(file_pair[1])
            df_right = process_data_file(file_pair[2])
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

        for file_pair in file_pairs:
            self.data2plot.append((file_pair[0], process_dfs(file_pair)))
        print(f"{len(self.data2plot)} pairs loaded")


class DataCompare:
    def __init__(self, d1, d2):
        self.data2plot = {}
        # TODO: change data2plot in DataSet to a dictionary
        d2_data2plot = {item[0]: item[1] for item in d2.data2plot}
        for item in d1.data2plot:
            if item[0] in d2_data2plot:
                d1_df_both = item[1][2]
                d2_df_both = d2_data2plot[item[0]][2]
                d1_df_stats = item[1][3]
                d2_df_stats = d2_data2plot[item[0]][3]
                # connect d1_df_both and d2_df_both
                # rename columns to avoid duplicates
                d1_df_both.rename(
                    columns={"Left Mean": "Left Mean 1", "Right Mean": "Right Mean 1"},
                    inplace=True,
                )
                d1_df_both["Left Mean 2"] = d2_df_both["Left Mean"]
                d1_df_both["Right Mean 2"] = d2_df_both["Right Mean"]
                # connect d1_df_stats and d2_df_stats
                # rename columns to avoid duplicates
                d1_df_stats.rename(
                    columns={
                        "Maximum": "Maximum 1",
                        "Minimum": "Minimum 1",
                        "Range": "Range 1",
                    },
                    inplace=True,
                )
                d1_df_stats["Maximum 2"] = d2_df_stats["Maximum"]
                d1_df_stats["Minimum 2"] = d2_df_stats["Minimum"]
                d1_df_stats["Range 2"] = d2_df_stats["Range"]
                self.data2plot[item[0]] = (d1_df_both, d1_df_stats)


class Plot:
    def __init__(self, d, param=None, src=None):
        params = [item[0] for item in d.data2plot]
        if param:
            index = params.index(param)
            self.plot(
                param, d.data2plot[index][1], c.colors, c.size, "kinematics", src=src
            )
        else:
            # use multiselect to choose parameters to plot
            self.params2plot = st.multiselect(
                "You can choose multiple parameters to plot", params
            )
            for item in d.data2plot:
                if item[0] in self.params2plot:
                    self.plot(item[0], item[1], c.colors, c.size, "kinematics", src="")

    def plot(self, bioparameter, dfs, colors, size, kind, src):
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
                x_range=Range1d(
                    start=0, end=100
                ),  # Limit the x-axis, default (-5, 105)
            )
            p.border_fill_color = "seashell"
            p.xaxis.axis_label_text_font_style = p.yaxis.axis_label_text_font_style = (
                "normal"
            )
            p.xaxis.axis_label_text_font_size = p.yaxis.axis_label_text_font_size = (
                "14px"
            )
            p.toolbar.logo = None
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

        st.header(f"{bioparameter} {src}")
        opts = ["Left", "Right", "Both"]
        foot2plot = st.radio(
            f"Show plot for {bioparameter} {src}", opts, horizontal=True, index=2
        )
        plot_df(dfs[opts.index(foot2plot)], foot2plot, kind)
        st.dataframe(dfs[3], hide_index=True)


class PlotCompare:
    def __init__(self, dc, param):
        self.plot_compare(dc.data2plot[param][0], dc.data2plot[param][1], param)

    def plot_compare(self, df_both, df_stats, param):
        st.header(f"{param}")
        st.dataframe(df_stats, hide_index=True)
        p = figure(
            x_axis_label="Gait cycle, %",
            y_axis_label="Angle, degrees",
            height=c.size["height"],
            width=c.size["width"],
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
        p.toolbar.logo = None
        lines, labels = [], []
        for col in range(1, len(df_both.columns)):
            column = df_both.columns[col]
            line_dash = "solid" if "Mean 1" in column else "dashed"
            width = 2
            color = "blue" if "Left" in column else "red"
            line = p.line(
                "Gait cycle",
                column,
                source=ColumnDataSource(df_both),
                color=color,
                width=width,
                name=column,
                line_dash=line_dash,
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
            height=c.size["height"],
            width=c.size["width"],
        )
