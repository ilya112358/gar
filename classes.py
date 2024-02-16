import os
import toml
import pandas as pd


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
    def __init__(self, directory, valid_files):
        file_pairs = []
        self.data2plot = []
        for item in valid_files:
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

        for file_pair in file_pairs:
            self.data2plot.append(
                    (file_pair[0], process_dfs(file_pair))
                )        
        print(f"{len(self.data2plot)} pairs loaded")
