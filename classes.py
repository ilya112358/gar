from bokeh.embed import file_html
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Legend, Range1d, Band
from bokeh.models.tickers import SingleIntervalTicker
from bokeh.palettes import viridis

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import toml

from io import BytesIO


class Config:
    file = "config.toml"

    def __init__(self):
        with open(self.file, "r") as f:
            self.config = toml.load(f)
        self.info = self.config["info"]
        self.temporal = self.config["temporal"]
        self.gps = self.config["gps"]
        self.kinematics = self.config["kinematics"]
        self.layout = self.config["standard"]["layout"]
        self.colors = self.config["colors"]
        self.size = self.config["size"]
        keys = self.config["phases"]["names"]
        values = self.config["phases"]["ranges"]
        self.phases = dict(zip(keys, values))


c = Config()


class DataSet:
    """
    Load, process and organize gait analysis data for visualization.

    This class takes raw DataFrames for various exported files
    (metadata, temporal/spatial parameters, gait profile scores, kinematics)
    and produces ready-to-plot structures

    Parameters
    ----------
    d : dict of str -> pandas.DataFrame
        Mapping from expected file identifiers (e.g. `"Info.txt"`, 
        `"Temporal Distance.txt"`, kinematics filenames) to their raw
        DataFrame contents.

    Attributes
    ----------
    kinematics : dict
        For each gait parameter name, a dict with keys:
        - `"df_left"`, `"df_right"`: DataFrames of mean curves per side  
        - `"df_both"`: combined side curves  
        - `"df_norm"`: normalized curves (if available)  
        - `"df_stats"`: summary statistics (max, min, ROM)  
        - `"y_axis"`: [ymin, ymax] for plotting limits  

    info : pandas.DataFrame
        Subject metadata table with columns `["Metadata", "Value"]`,
        extracted from the Info file (name, date, test condition, etc.).

    ts : pandas.DataFrame
        Temporal and spatial parameters (speed, cadence, step length, stance %, etc.),
        organized in a tidy table with columns `["Parameters", "Both", "Left", "Right"]`.

    gps : tuple of (float, pandas.DataFrame)
        - Overall Gait Profile Score (mean across metrics)  
        - Per-metric Gait Variable Score summary as a DataFrame with columns
          `["Metric", "Left", "Right"]`.
    """

    def __init__(self, d: dict):
        self.kinematics = {}  # dictionary to store processed data for plotting
        if c.info['file'] not in d:
            st.error(f"File {c.info['file']} not found")
            st.stop()
        self.process_info(d[c.info['file']])
        if c.temporal['file'] not in d:
            cols = ["Parameters", "Both", "Left", "Right"]
            self.ts = pd.DataFrame([{c: np.nan for c in cols}])            
        else:
            self.ts = self.process_ts(d[c.temporal['file']])
        if c.gps['file'] not in d:
            cols = ["Metrics", "Left", "Right"]
            self.gps = (np.nan, pd.DataFrame([{c: np.nan for c in cols}]))
        else:
            self.gps = self.process_map(d[c.gps['file']])
        for item in c.kinematics:
            if item["left_file"] not in d or item["right_file"] not in d:
                continue
            self.kinematics[item["name"]] = self.process_dfs(
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
        self.title = f"{dct['First Name']} {dct['Last Name']}, {dct['Creation date']}, {dct['Test condition']}"
        self.info = pd.DataFrame(dct.items(), columns=['Metadata', 'Value'])

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
    
    def process_map(self, df):
        df = (
            df
            .iloc[:, 1:]                     # drop the first column
            .rename(columns=df.iloc[0])      # promote row 0 to header
            .iloc[4:]                        # drop rows 0–3
            .reset_index(drop=True)          # re‑index 0…n‑1
        )
        row = df.iloc[0]
        # Define GPS summary and all GVS median variables
        gps_cols = ['Left_GPS_mean_MEAN', 'Right_GPS_mean_MEAN']
        gvs_cols = [col for col in df.columns if col.endswith('_gvs_MEDIAN')]
        # Combine and build a tidy record list
        records = []
        for col in gps_cols + gvs_cols:
            if col.startswith(('Left_', 'Right_')):
                side_label, metric = col.split('_', 1)
            else:
                side_label, metric = col.split(' ', 1)
            records.append({
                'metric': metric,
                'side': side_label,
                'value': row[col]
            })
        overall = row['Overall_GPS_mean_MEAN']
        tidy_df = pd.DataFrame(records)
        pivoted = tidy_df.pivot(index='metric', columns='side', values='value').reset_index()
        # Rename metrics
        old_to_new = {
            'GPS_mean_MEAN': 'Gait Profile Score',
            'Pelvic Angles_X_gvs_MEDIAN': "Pelvis Tilt",
            'Pelvic Angles_Y_gvs_MEDIAN': "Pelvis Obl",
            'Pelvic Angles_Z_gvs_MEDIAN': "Pelvis Rot",
            'Hip Angles_X_gvs_MEDIAN': 'Hip Fle/Ext',
            'Hip Angles_Y_gvs_MEDIAN': 'Hip Add/Abd',
            'Hip Angles_Z_gvs_MEDIAN': 'Hip Rot',
            'Knee Angles_X_gvs_MEDIAN': "Knee Fle/Ext",
            'Ankle Angles_X_gvs_MEDIAN': 'Ankle Dor/Pla',
            'Foot Progression_Z_gvs_MEDIAN': 'Foot Prog',
        }
        pivoted['metric'] = pivoted['metric'].map(old_to_new).fillna(pivoted['metric'])
        desired_order = list(old_to_new.values())
        pivoted = (
            pivoted
            .set_index('metric')      # make metrics the index…
            .loc[desired_order]       # …and pick them in the right order
            .reset_index()            # back to a normal column
        )
        pivoted.rename(columns={'metric':'Metric'}, inplace=True)
        return (overall, pivoted)

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

    def __init__(self, d1: DataSet, d2: DataSet):
        self.data2plot = {}
        for item in d1.kinematics:
            if item in d2.kinematics:
                d_df_both = d1.kinematics[item]["df_both"].copy()
                d2_df_both = d2.kinematics[item]["df_both"]
                d_df_stats = d1.kinematics[item]["df_stats"].copy()
                d2_df_stats = d2.kinematics[item]["df_stats"]
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
        # Create a copy of the DataFrame to avoid modifying the original
        df_norm_copy = df_norm.copy()
        
        # Calculate 1SD boundaries
        df_norm_copy["Mean - SD"] = df_norm_copy["Mean"] - df_norm_copy["SD"]
        df_norm_copy["Mean + SD"] = df_norm_copy["Mean"] + df_norm_copy["SD"]
        
        # Calculate 2SD boundaries
        df_norm_copy["Mean - 2SD"] = df_norm_copy["Mean"] - 2 * df_norm_copy["SD"]
        df_norm_copy["Mean + 2SD"] = df_norm_copy["Mean"] + 2 * df_norm_copy["SD"]
        
        # Duplicate 'Mean' column as 'Normative' for tooltip reference
        df_norm_copy["Normative"] = df_norm_copy["Mean"]
        
        # Add the 2SD band with a more transparent gray fill
        band_2sd = Band(
            base="Gait cycle",
            lower="Mean - 2SD",
            upper="Mean + 2SD",
            source=ColumnDataSource(df_norm_copy),
            fill_color="gray",
            fill_alpha=0.15,  # more transparent than the 1SD band
        )
        self.figure.add_layout(band_2sd)
        
        # Add the 1SD band (drawn on top of the 2SD band)
        band_1sd = Band(
            base="Gait cycle",
            lower="Mean - SD",
            upper="Mean + SD",
            source=ColumnDataSource(df_norm_copy),
            fill_color="gray",
            fill_alpha=0.25,
        )
        self.figure.add_layout(band_1sd)
        
        # Add a line for the actual mean value using the 'Normative' column
        self.figure.line(
            "Gait cycle",
            "Normative",
            source=ColumnDataSource(df_norm_copy),
            color="dimgray",
            width=2,
            line_dash="dashed",
            name="Normative"
        )

    def add_band_classic(self, df_norm):
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
    """Individual parameter plot"""

    def __init__(self, dataset_key: str):
        self.d = st.session_state[dataset_key]  # DataSet
        self.config_key = f"{dataset_key}_Plot" # "d1_Plot"
        # Initialize or load self.state
        if self.config_key not in st.session_state["plot_configs"]:
            st.session_state["plot_configs"][self.config_key] = {
                "selected_param": None,
            }
        self.state = st.session_state["plot_configs"][self.config_key]
        # Use persistent selected_param or default to first option
        default_idx = 0
        if self.state["selected_param"] and self.state["selected_param"] in self.d.kinematics:
            default_idx = list(self.d.kinematics.keys()).index(self.state["selected_param"])        
        param2plot = st.selectbox(
            "You can choose one parameter to plot", 
            tuple(self.d.kinematics.keys()),
            index=default_idx,
            key=f"{self.config_key}_param_select"            
        )
        # Update state when parameter changes
        if param2plot != self.state["selected_param"]:
            self.state["selected_param"] = param2plot
        # Plot and show stats and comments
        if param2plot is not None:
            dfs = self.d.kinematics[param2plot]
            self.plot(param2plot, dfs)
            self.showstats(param2plot, dfs)

    def plot(self, bioparameter, dfs):
        st.markdown(f"### {bioparameter}")
        opts = ["Left", "Right", "Both"]
        foot2plot = st.radio(f"Show plot for {bioparameter}", opts, horizontal=True, index=2)
        fig = Figure(y_axis=dfs["y_axis"])
        labels = []
        df = dfs[{"Left": "df_left", "Right": "df_right", "Both": "df_both"}[foot2plot]]
        palette = viridis(len(df.columns) - 3)  # -(1st, Static, Mean)
        for col in range(1, len(df.columns)):
            column = df.columns[col]
            if foot2plot == "Both":
                if column == "Left Mean":
                    color = c.colors["left"]
                elif column == "Right Mean":
                    color = c.colors["right"]
                else:
                    color = c.colors["mean"]  # black in case column names change
                line = fig.add_line(df, column, color, 3)
            else:
                if column == "Static":
                    color = c.colors["static"]
                elif "Mean" in column:
                    continue  # add in diff style?
                else:
                    color = palette[col - 1]
                line = fig.add_line(df, column, color, 2)
            labels.append((column, [line]))
        df_norm = dfs["df_norm"]
        if df_norm is not None:
            fig.add_band(df_norm)
        fig.add_legend(labels)
        fig.render()
        st.markdown("(dashed gray line: normative Mean values, dark gray band: ±1 SD, light gray band: ±2 SD)")

    def showstats(self, param2plot: str, dfs: dict):
        st.markdown("##### Analysis")
        st.markdown("Table below shows maximum, minimum and range of motion for the left (L) and right (R) side during main gait cycle phases.")
        st.markdown("You can edit the first three columns to customize gait cycle phases.")
        st.markdown("It is also possible to copy and paste gait cycle phases from an Excel file.")

        self.state.setdefault("analysis_by_param", {})  # persistent stats and comments

        def calc_stats(phases: dict):
            """Create a combined dataframe for all phases: {'Full Cycle': (0, 100),}"""
            df_combined = pd.DataFrame()
            for key, value in phases.items():
                df_stats = DataSet.create_df_stats(dfs["df_left"], dfs["df_right"], phase=key, frames=value)
                df_combined = pd.concat([df_combined, df_stats], ignore_index=True)
            return df_combined
  
        # Initialize or restore state for this specific parameter
        if param2plot not in self.state["analysis_by_param"]:
            self.state["analysis_by_param"][param2plot] = {
                "df_stats": calc_stats(c.phases),
                "comments": "",
                "needs_reset": False  # Parameter-specific reset flag
            }
        # Get reference to this parameter's state
        param_state = self.state["analysis_by_param"][param2plot]

        # Reset stats if needed for this specific parameter
        if param_state.get("needs_reset", False):
            param_state["df_stats"] = calc_stats(c.phases)
            param_state["comments"] = ""
            param_state["needs_reset"] = False  # Clear the reset flag

        def force_reset():
            param_state["needs_reset"] = True

        st.button("Reset stats and comments", on_click=force_reset, key=f"{self.config_key}_{param2plot}_reset_btn")

        # data_editor columns: 'required' to accept the row, 'disabled' to edit
        no_edit = st.column_config.Column(disabled=True)
        column_config = {
            "Phase": st.column_config.Column(required=True),
            "% Start": st.column_config.NumberColumn(required=True, min_value=0, max_value=100),
            "% End": st.column_config.NumberColumn(required=True, min_value=0, max_value=100),
            "L Max": no_edit, "L Min": no_edit, "L ROM": no_edit,
            "R Max": no_edit, "R Min": no_edit, "R ROM": no_edit,
            "Δ Max": no_edit, "Δ Min": no_edit, "Δ ROM": no_edit,
        }
        editor_key = f"{self.config_key}_{param2plot}_editor"

        def df_on_change():
            """synchronize df_stats to data_editor"""
            state = st.session_state[editor_key]
            df = param_state["df_stats"]
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
            param_state["df_stats"] = calc_stats(phases)
        
        st.data_editor(
            param_state["df_stats"], 
            key=editor_key,
            on_change=df_on_change,
            column_config=column_config, 
            hide_index=True, 
            num_rows="dynamic"
        )

        comments_key = f"{self.config_key}_{param2plot}_comments"
        comments = st.text_area(
            "You may write a short analysis here", 
            value=param_state["comments"],
            key=comments_key
        )
        # Update comments in state when changed
        if comments != param_state["comments"]:
            param_state["comments"] = comments

        # Checkbox to include in Excel report
        checked = param2plot in self.state.get("add_to_rep", {})
        if st.checkbox(
            f"Include {param2plot} in Excel report", 
            value=checked,
            key=f"{self.config_key}_{param2plot}_include"
        ):
            self.state.setdefault("add_to_rep", {})
            self.state["add_to_rep"][param2plot] = {
                "df_stats": param_state["df_stats"], 
                "comments": param_state["comments"]
            } 
        else:
            if "add_to_rep" in self.state and param2plot in self.state["add_to_rep"]:
                del self.state["add_to_rep"][param2plot]


class PlotLayout:
    """Plot graphs in standard layout"""

    def __init__(self, d: DataSet):
        st.markdown("This is summary grid for Kinematic values")
        st.markdown("All graphs show mean values, :red[red for Left] and :blue[blue for Right]")
        st.markdown("Gray bands show normative means ±1 standard deviation")
        st.markdown("Check [interactive plots](#interactive-plots) to see more data")

        height = c.size["small_height"]
        width = c.size["small_width"]
        figs = {}
        for param, dfs in d.kinematics.items():
            fig = Figure(height=height, width=width, y_axis=dfs["y_axis"])
            fig.figure.tools = []
            df = dfs["df_both"]
            for col in range(1, len(df.columns)):
                column = df.columns[col]
                if column == "Left Mean":
                    color = c.colors["left"]
                elif column == "Right Mean":
                    color = c.colors["right"]
                else:
                    color = c.colors["mean"]  # black in case column names change
                fig.add_line(df, column, color, 2)
            df_norm = dfs["df_norm"]
            if df_norm is not None:
                fig.add_band_classic(df_norm)
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
                    # placeholder in the layout
                    empty = Figure(height=height, width=width)
                    empty.figure.tools = []
                    # Add a dummy invisible renderer to suppress the missing renderers warning
                    empty.figure.circle([], [], alpha=0)
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


class Export:
    """
    Collects multiple DataFrame sections and writes them
    into a single Excel sheet, returning a bytes payload.
    """
    def __init__(
        self,
        title: str,
        info_df: pd.DataFrame,
        ts_df: pd.DataFrame,
        stats_map: dict,
        sheet_name: str
    ):
        self.title = title
        self.info_df = info_df
        self.ts_df = ts_df
        self.stats_map = stats_map
        self.sheet_name = sheet_name

        # In-memory workbook setup
        self.output = BytesIO()
        self.writer = pd.ExcelWriter(self.output, engine="xlsxwriter")
        self.workbook = self.writer.book
        self.worksheet = self.workbook.add_worksheet(self.sheet_name)
        self.bold = self.workbook.add_format({"bold": True})

        # layout: start writing data at row 2 (title goes at row 0)
        self.current_row = 2
        self.worksheet.set_column(0, 0, 20)

    def write_title(self):
        self.worksheet.write_string(0, 0, self.title, self.bold)

    def write_info(self):
        self.info_df.to_excel(
            self.writer,
            sheet_name=self.sheet_name,
            startrow=self.current_row,
            index=False
        )
        self.current_row += self.info_df.shape[0] + 2

    def write_time_spatial(self):
        self.ts_df.to_excel(
            self.writer,
            sheet_name=self.sheet_name,
            startrow=self.current_row,
            index=False
        )
        self.current_row += self.ts_df.shape[0] + 2

    def write_stats(self):
        for param, block in self.stats_map.items():
            # header
            self.worksheet.write_string(self.current_row, 0, param, self.bold)
            self.current_row += 1

            # stats table
            df_stats = block["df_stats"]
            df_stats.to_excel(
                self.writer,
                sheet_name=self.sheet_name,
                startrow=self.current_row,
                index=False
            )
            self.current_row += df_stats.shape[0] + 2

            # comments
            self.worksheet.write_string(
                self.current_row, 0, block.get("comments", "")
            )
            self.current_row += 2

    def save(self) -> bytes:
        self.writer.close()
        return self.output.getvalue()

    def export(self) -> bytes:
        """Write everything and return raw Excel bytes in one call."""
        self.write_title()
        self.write_info()
        self.write_time_spatial()
        self.write_stats()
        return self.save()

    @classmethod
    def to_bytes(
        cls,
        dataset: DataSet, 
        stats_map: dict,
        sheet_name: str = "Sheet1"
    ) -> bytes:
        """
        Convenience entrypoint: do one call from Streamlit:
           Export.to_bytes(...)
        """
        exporter = cls(dataset.title, dataset.info, dataset.ts, stats_map, sheet_name)
        return exporter.export()
