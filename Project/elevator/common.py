from enum import IntEnum
import logging
from configparser import ConfigParser


class Direction(IntEnum):
    Up = 1,
    Stop = 0,
    Down = -1


class Config(object):

    def __init__(self, file_path):
        logging.debug("Begin reading the configuration")

        # Opens and parses the configuration file
        self.reader = ConfigParser()
        success = self.reader.read(file_path)

        if len(success) == 0:
            logging.fatal("Cannot open the configuration (%s)" % (file_path))
            raise RuntimeError()

        self.floors = self.reader.read("system", "floors")

        logging.debug("End reading the configuration")
