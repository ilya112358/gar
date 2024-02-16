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
