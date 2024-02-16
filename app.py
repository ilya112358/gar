import streamlit as st
import toml


class Config:
    __file = "config.toml"

    def __init__(self):
        with open(self.__file, "r") as f:
            self.__config = toml.load(f)
        self.kinematics = self.__config["kinematics"]
        self.colors = self.__config["colors"]
        self.size = self.__config["size"]


st.set_page_config(
    page_title="Gait Analysis Report", layout="wide"
)  # not a central column
st.image("GAR_topimage.jpg", width=512)
st.title("Gait Analysis Report")
st.text("This is where the data from Visual3D gets visualized")
st.write("---")
st.write("<< Choose measurement page one or two to load and visualize data.")
c = Config()
# st.write(dir(c))