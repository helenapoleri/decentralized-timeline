import os
import configparser

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)),
            'config/configuration.ini'))

BOOTSTRAP_NODES = config["BOOTSTRAP"]["INITIAL_NODES"]
DISCARD_BASELINE = int(config["CONTROL"]["DISCARD_BASELINE"])
HIERARCHY_BASELINE = int(config["CONTROL"]["HIERARCHY_BASELINE"])
REDIRECT_USERS = int(config["CONTROL"]["REDIRECT_USERS"])
