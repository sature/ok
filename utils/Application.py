from configparser import ConfigParser


class Application:

    config = None

    @staticmethod
    def read_config(f):
        Application.config = ConfigParser()
        Application.config.read(f)
