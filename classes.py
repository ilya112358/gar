from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Legend, Range1d, Label, Band
from bokeh.models.tickers import SingleIntervalTicker

import os
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import toml

from io import BytesIO

class Config:
    __file = "config.toml"

    def __init__(self):
        with open(self.__file, "r") as f:
            self.__config = toml.load(f)
        self.kinematics = self.__config["kinematics"]
        self.layout = self.__config["standard"]["layout"]
        self.colors = self.__config["colors"]
        self.size = self.__config["size"]
        keys = self.__config["phases"]["names"]
        values = self.__config["phases"]["ranges"]
        self.phases = dict(zip(keys, values))


c = Config()


class DataSet:
    """
    A class used to represent a DataSet for processing and plotting.

    Attributes
    ----------
    data2plot : dict
        A dictionary to store processed data for plotting.
        Each key is a parameter name, and each value is a dictionary containing the processed dataframes
        for left, right, both, optionally norm, stats and y-axis limits.
    info : dict
        A dictionary containing metadata extracted from the "Info.txt" file.
    ts : dict
        A dictionary containing temporal and spatial data from the "Temporal Distance.txt" file.
    """

    def __init__(self, d):
        self.data2plot = {}  # dictionary to store processed data for plotting
        if "Info.txt" not in d:
            st.error("File Info.txt not found")
            st.stop()
        self.info = self.process_info(d["Info.txt"])  # Metadata
        if "Temporal Distance.txt" not in d:
            self.ts = {"Error": "File Temporal Distance.txt not found"}
        else:
            self.ts = self.process_ts(d["Temporal Distance.txt"])
        for item in c.kinematics:
            if item["left_file"] not in d or item["right_file"] not in d:
                continue
            self.data2plot[item["name"]] = self.process_dfs(
                {
                    "left": d[item["left_file"]],
                    "right": d[item["right_file"]],
                    "norm": d[item["norm_file"]] if item["norm_file"] in d else None,
                    "y_axis": item["y_axis"] if "y_axis" in item else None,
                }
            )
    
    def process_info(self, df):
        # Remove first col (index), use first row as keys, fifth as values
        df = df.iloc[:, 1:]
        keys = df.loc[0].tolist()
        values = df.loc[4].tolist()
        dct = dict(zip(keys, values))
        # check if there is the key "Folder Name", take the name of the last folder from the value and split into subsession and test condition
        if "Folder Name" in dct:
            dct["Subsession"], dct["Test condition"] = (dct["Folder Name"].split("\\")[-2]).split("_")
            del dct["Folder Name"]
        return dct

    def process_ts(self, df):
        # Remove first col (index), use first row as keys, fifth as values
        df = df.iloc[:, 1:]
        keys = df.loc[0].tolist()
        values = [float(v) for v in df.loc[4].tolist()]
        dct = dict(zip(keys, values))
        # values from QRC
        leftright = {
            "Step Length, cm": (round(dct['Left_Step_Length_Mean']*100, 0), round(dct['Right_Step_Length_Mean']*100, 0)),
            "Step Time, s": (round(dct['Left_Step_Time_Mean'], 2), round(dct['Right_Step_Time_Mean'], 2)),
            "Stance, %": (round(dct['Left_Stance_Time_Mean']/dct['Left_Cycle_Time_Mean'] * 100, 1), round(dct['Right_Stance_Time_Mean']/dct['Right_Cycle_Time_Mean'] * 100, 1)),
            "Initial Double Limb Support, %": (
                round(dct['Right_Terminal_Double_Limb_Support_Time_Mean']/dct['Left_Cycle_Time_Mean'] * 100, 1),
                round(dct['Right_Initial_Double_Limb_Support_Time_Mean']/dct['Right_Cycle_Time_Mean'] * 100, 1),
            ),
        }
        both = {
            "Speed, m/s": round(dct['Speed'], 2),
            "Cadence, steps/min": round((dct['Left_Steps_Per_Minute_Mean'] + dct['Right_Steps_Per_Minute_Mean'])/2, 0),
            "Cycle Time, s": round(dct['Cycle_Time_Mean'], 2),
            "Stride Length, cm": round(dct['Stride_Length_Mean']*100, 0),
            "Stride Width, cm": round(dct['Stride_Width_Mean']*100, 1),
        }
        df_ts = pd.DataFrame(
            {
                "Parameters": list(both.keys()) + list(leftright.keys()),
                "Both": list(both.values()) + [np.nan] * len(leftright),
                "Left": [np.nan] * len(both) + [v[0] for v in leftright.values()],
                "Right": [np.nan] * len(both) + [v[1] for v in leftright.values()],
            }
        )
        return df_ts
    
    def process_dfs(self, file_pair):
        df_left = self.process_data_file(file_pair["left"])
        df_right = self.process_data_file(file_pair["right"])
        df_left.rename(columns={df_left.columns[-1]: "Left Mean"}, inplace=True)
        df_right.rename(columns={df_right.columns[-1]: "Right Mean"}, inplace=True)
        # combine Gait cycle and two Mean columns to plot both
        df_both = pd.concat(
            [df_left.iloc[:, :1], df_left.iloc[:, -1:], df_right.iloc[:, -1:]],
            axis=1,
        )
        if file_pair["norm"] is not None:
            df_norm = self.process_norm(file_pair["norm"])
        else:
            df_norm = None
        df_stats = DataSet.create_df_stats(df_left, df_right)
        # y_axis is a list of min and max values for the y-axis
        y_axis = [
            min(
                df_left["Left Mean"].min(),
                df_right["Right Mean"].min(),
                file_pair["y_axis"][0],
            ),
            max(
                df_left["Left Mean"].max(),
                df_right["Right Mean"].max(),
                file_pair["y_axis"][1],
            ),
        ]
        return {
            "df_left": df_left,
            "df_right": df_right,
            "df_both": df_both,
            "df_norm": df_norm,
            "df_stats": df_stats,
            "y_axis": y_axis,
        }

    def process_data_file(self, df):
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

    def process_norm(self, df):
        # Remove first 4 text rows (headers)
        df = df.drop(df.index[:4])
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.rename(columns={df.columns[0]: "Gait cycle"}, inplace=True)
        df["Gait cycle"] -= 1
        df.rename(columns={df.columns[1]: "Mean"}, inplace=True)
        df.rename(columns={df.columns[2]: "SD"}, inplace=True)
        return df

    @classmethod
    def create_df_stats(cls, df_left, df_right, phase="Full Cycle", frames=(0, 100)):
        # start after end
        if frames[0] > frames[1]:
            # need [] for df otherwise index required
            return pd.DataFrame(
                {
                    "Phase": [phase],
                    "% Start": [frames[0]], 
                    "% End": [frames[1]],
                    "L Max": [np.nan], 
                    "L Min": [np.nan],
                    "L ROM": [np.nan],
                    "R Max": [np.nan], 
                    "R Min": [np.nan],
                    "R ROM": [np.nan],
                    "Δ Max": [np.nan],
                    "Δ Min": [np.nan],
                    "Δ ROM": [np.nan],
                }
            )

        df_left = df_left.loc[
            (df_left["Gait cycle"] >= frames[0]) & (df_left["Gait cycle"] <= frames[1])
        ]
        df_right = df_right.loc[
            (df_right["Gait cycle"] >= frames[0]) & (df_right["Gait cycle"] <= frames[1])
        ]

        def stats(df, col):
            try:
                idxmax = df[col].idxmax()
                mx = round(df.loc[idxmax, col], 1)
                idxmin = df[col].idxmin()
                mn = round(df.loc[idxmin, col], 1)
                rm = round(mx - mn, 1)
                return mx, mn, rm
            except ValueError:
                return np.nan, np.nan, np.nan

        stats_left = stats(df_left, "Left Mean")
        stats_right = stats(df_right, "Right Mean")
        return pd.DataFrame(
            {
                "Phase": [phase],
                "% Start": [frames[0]], 
                "% End": [frames[1]],
                "L Max": [stats_left[0]], 
                "L Min": [stats_left[1]],
                "L ROM": [stats_left[2]],
                "R Max": [stats_right[0]], 
                "R Min": [stats_right[1]],
                "R ROM": [stats_right[2]],
                "Δ Max": [stats_left[0] - stats_right[0]],
                "Δ Min": [stats_left[1] - stats_right[1]],
                "Δ ROM": [stats_left[2] - stats_right[2]],
            }
        )



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
                d_df_both = d1.data2plot[item]["df_both"].copy()
                d2_df_both = d2.data2plot[item]["df_both"]
                d_df_stats = d1.data2plot[item]["df_stats"].copy()
                d2_df_stats = d2.data2plot[item]["df_stats"]
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
                # d_df_stats.rename(
                #     columns={
                #         "Maximum": "Maximum 1",
                #         "Minimum": "Minimum 1",
                #         "Range": "Range 1",
                #     },
                #     inplace=True,
                # )
                # d_df_stats["Maximum 2"] = d2_df_stats["Maximum"]
                # d_df_stats["Minimum 2"] = d2_df_stats["Minimum"]
                # d_df_stats["Range 2"] = d2_df_stats["Range"]
                self.data2plot[item] = {"df_both": d_df_both, "df_stats": d_df_stats}


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
    add_band(df_norm):
        Adds a gray band to the figure.
    add_legend(labels):
        Adds a legend to the figure.
    render():
        Renders the figure as an HTML component.
    """

    def __init__(
        self,
        y_axis=None,
        x_label="Gait cycle, %",
        y_label="Angle, degrees",
        height=c.size["height"],
        width=c.size["width"],
    ):
        self.figure = figure(
            x_axis_label=x_label,
            y_axis_label=y_label,
            height=height,
            width=width,
            tools="pan, box_zoom, reset",
            # will {Gait cycle} work for GRF?
            tooltips="[$name] @$name{0.00} at @{Gait cycle}%",  # [Mean] -0.77 at 33%
            toolbar_location="above",
            x_range=(0, 100),  # Limit the x-axis, default (-5, 105)
        )
        if y_axis is not None:
            self.figure.y_range = Range1d(y_axis[0], y_axis[1])
        self.figure.border_fill_color = "seashell"
        self.figure.xaxis.axis_label_text_font_style = "normal"
        self.figure.yaxis.axis_label_text_font_style = "normal"
        self.figure.xaxis.axis_label_text_font_size = "14px"
        self.figure.yaxis.axis_label_text_font_size = "14px"
        self.figure.xaxis.ticker = SingleIntervalTicker(interval=10)
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

    def add_band(self, df_norm):
        df_norm["Mean - SD"] = df_norm["Mean"] - df_norm["SD"]
        df_norm["Mean + SD"] = df_norm["Mean"] + df_norm["SD"]
        band = Band(
            base="Gait cycle",
            lower="Mean - SD",
            upper="Mean + SD",
            source=ColumnDataSource(df_norm),
            fill_color="gray",
            fill_alpha=0.25,
        )
        self.figure.add_layout(band)

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
        param2plot = st.selectbox(
            "You can choose one parameter to plot", 
            tuple(d.data2plot.keys()),
            index=None,
        )
        if "add_to_rep" not in st.session_state:
            st.session_state["add_to_rep"] = {}
        if param2plot is not None:
            dfs = d.data2plot[param2plot]
            self.plot(param2plot, dfs)
            self.showstats(param2plot, dfs)

    def plot(self, bioparameter, dfs):
        st.markdown(f"### {bioparameter}")
        opts = ["Left", "Right", "Both"]
        foot2plot = st.radio(f"Show plot for {bioparameter}", opts, horizontal=True, index=2)
        fig = Figure(y_axis=dfs["y_axis"])
        labels = []
        df = dfs[{"Left": "df_left", "Right": "df_right", "Both": "df_both"}[foot2plot]]
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
        df_norm = dfs["df_norm"]
        if df_norm is not None:
            fig.add_band(df_norm)
        fig.add_legend(labels)
        fig.render()

    def showstats(self, param2plot, dfs):

        def calc_stats(phases):
            "Create a combined dataframe for all phases: dict {'Full Cycle': (0, 100),}"

            df_combined = pd.DataFrame()
            for key, value in phases.items():
                df_stats = DataSet.create_df_stats(dfs["df_left"], dfs["df_right"], phase=key, frames=value)
                df_combined = pd.concat([df_combined, df_stats], ignore_index=True)
            return df_combined
        
        st.markdown("###### Mean value statistics")
        st.markdown("Table below shows maximum, minimum and range of motion for left (L) and right (R) side during main gait cycle phases.")
        st.markdown("You can edit the first three columns to customize gait cycle phases.")
        st.markdown("It is also possible to copy and paste gait cycle phases from an Excel file.")

        # first run or reset or param2plot changed
        if "df_stats" not in st.session_state or st.session_state["reset_stats"] or param2plot != st.session_state["param2plot"]:
            st.session_state["df_stats"] = calc_stats(c.phases)
            st.session_state["reset_stats"] = False
            st.session_state["param2plot"] = param2plot
            if "analysis" in st.session_state:
                st.session_state["analysis"] = ""

        def force_reset():
            st.session_state["reset_stats"] = True

        st.button("Reset stats and analysis", on_click=force_reset)

        # data_editor columns: 'required' to accept the row, 'disabled' to edit
        column_config = {
            "Phase": st.column_config.Column(required=True),
            "% Start": st.column_config.NumberColumn(required=True, min_value=0, max_value=100),
            "% End": st.column_config.NumberColumn(required=True, min_value=0, max_value=100),
            "L Max": st.column_config.Column(disabled=True), "L Min": st.column_config.Column(disabled=True), "L ROM": st.column_config.Column(disabled=True),
            "R Max": st.column_config.Column(disabled=True), "R Min": st.column_config.Column(disabled=True), "R ROM": st.column_config.Column(disabled=True),
            "Δ Max": st.column_config.Column(disabled=True), "Δ Min": st.column_config.Column(disabled=True), "Δ ROM": st.column_config.Column(disabled=True),
        }

        def df_on_change():
            "change df_stats to fit df_editor, called from on_change="

            state = st.session_state["df_editor"]
            df = st.session_state["df_stats"]
            # Edited
            for index, updates in state["edited_rows"].items():
                for key, value in updates.items():
                    df.loc[index, key] = value
            # Added
            for row in state["added_rows"]:
                df.loc[len(df)] = row
                df.reset_index(drop=True, inplace=True)
            # Deleted
            for index in state["deleted_rows"]:
                df.drop(index, inplace=True)
            phases = dict(zip(df["Phase"], zip(df["% Start"], df["% End"])))
            df_stats = calc_stats(phases)
            st.session_state["df_stats"] = df_stats

        st.data_editor(st.session_state["df_stats"], key="df_editor", on_change=df_on_change,
                       column_config=column_config, hide_index=True, num_rows="dynamic")

        st.text_area("You may write a short analysis here", key="analysis")

        # checkbox to include in Excel report
        checked = param2plot in st.session_state["add_to_rep"]
        if st.checkbox(f"Include {param2plot} in Excel report", value=checked):
            st.session_state["add_to_rep"][param2plot] = {"df_stats": st.session_state["df_stats"], "analysis": st.session_state["analysis"]} 
        else:
            if param2plot in st.session_state["add_to_rep"]:
                del st.session_state["add_to_rep"][param2plot]


class PlotLayout:
    """Plot graphs in standard layout"""

    def __init__(self, d):
        st.markdown("All graphs show mean values, :red[red for Left] and :blue[blue for Right]")
        st.markdown(":gray[Gray bands] show normative values +/- 1 SD")
        st.markdown("Check [individual plots](#individual-plots) to see consistency and relevant statistics")

        height = c.size["small_height"]
        width = c.size["small_width"]
        figs = {}
        for param, dfs in d.data2plot.items():
            fig = Figure(height=height, width=width, y_axis=dfs["y_axis"])
            df = dfs["df_both"]
            for col in range(1, len(df.columns)):
                column = df.columns[col]
                color = c.colors["color_list"][col - 1]
                fig.add_line(df, column, color, 2)
            df_norm = dfs["df_norm"]
            if df_norm is not None:
                fig.add_band(df_norm)
            fig.figure.title.text = param
            fig.figure.title.text_font_size = "16px"
            fig.figure.min_border_right = 20
            figs[param] = fig
        gridrows = []
        for row in c.layout:
            gridrow = []
            for param in row:
                if param in figs:
                    gridrow.append(figs[param].figure)
                else:
                    # empty plot with No data label
                    empty = Figure(height=height, width=width)
                    no_data_label = Label(
                        x=int(height / 2),
                        y=int(width / 3),
                        x_units="screen",
                        y_units="screen",
                        text="No data",
                    )
                    empty.figure.add_layout(no_data_label)
                    gridrow.append(empty.figure)
            gridrows.append(gridrow)
        grid = gridplot(gridrows, merge_tools=False, toolbar_options=dict(logo=None))
        components.html(
            file_html(
                # gridrows[0][0],
                grid,
                "cdn",
            ),
            # add some breathing space around the grid
            height=height * len(c.layout),
            width=width * len(c.layout[0]) + 50,
        )


class PlotCompare:
    """Plot the comparison of the two datasets"""

    def __init__(self, dc, param):
        self.plot_compare(
            dc.data2plot[param]["df_both"], dc.data2plot[param]["df_stats"], param
        )

    def plot_compare(self, df_both, df_stats, param):
        st.header(f"{param}")
        # st.dataframe(df_stats, hide_index=True)
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
