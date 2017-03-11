"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import configparser
import enum


class Direction(enum.IntEnum):
    """
    Direction of request from floors
    """

    Down = -1,
    Stop = 0,
    Up = 1


class Configuration(object):
    """
    Reads the configuration file. In this project, all the modules in each
    nodes and all the nodes in the system share the same configuration file.
    The configuration file can also contains node-specific settings which are
    also in the same file but different sections.
    """

    def __init__(self, path, node_name):
        """
        Initializes a new instance of the core.Configuration class.
        Parses the configuration file at `path` and overrides the settings
        by node-specific settings for the node `node_name`.

        @param path Path to configuration file to parse
        @param node_name Name of the node where the program is running
        """

        logging.debug("Start reading configuration file"
                      "(path = \"%s\", node_name = \"%s\")",
                      path, node_name)

        self.__config = dict()

        # Reads the configuration file
        logging.debug("Parse the configuration file")
        parser = configparser.ConfigParser()
        count = parser.read(path)
        if len(count) < 1:
            logging.fatal(
                "Cannot read the configuration file (path = \"%s\")", path)

            raise RuntimeError()

        # Saves the configuration to the dictionary
        # Overrides the generic settings by node-specific one if avaiable
        logging.debug("Import the configuration to dictionary")
        for section_name in parser.sections():
            parser_section = parser[section_name]

            # Checks if this is a generic or node-specific settings
            # Node-specific section: <section_part>.<node_part>
            parts = section_name.split(".")
            section_part = section_name
            node_part = str()

            if len(parts) == 2:  # This is node-specific settings
                section_part = parts[0]
                node_part = parts[1]
            elif len(parts) > 2:  # Invalid section name
                logging.fatal(
                    "Configuration format is wrong! (section_name = \"%s\")",
                    section_name)
                raise RuntimeError()

            # Creates new section in the dictionary if not available
            if section_part not in self.__config:
                self.__config[section_part] = dict()
            section = self.__config[section_part]

            # Copies the settings from file to the dictionary
            if node_part == "" or node_part == node_name:
                for config_name in parser_section:
                    section[config_name] = parser_section[config_name]

            if node_part != "":
                for config_name in parser_section:
                    section[node_part + "." + config_name] = \
                        parser_section[config_name]

        logging.info("Finish reading configuration file")

    def get_value(self, section_name, config_name, default_value=None):
        """
        Returns the configuration value of the setting in the specified section
        with the specified name. If the setting is not available, returns
        the default value if not None, else throws RuntimeError.
        """

        logging.debug("Start getting configuration value "
                      "(section_name = \"%s\", config_name = \"%s\")",
                      section_name, config_name)

        # Finds and returns the settings
        value = default_value

        if section_name in self.__config:
            section = self.__config[section_name]
            if config_name in section:
                value = section[config_name]

        if value is None:
            logging.fatal(
                "Configuration not found! (section_name = \"%s\", "
                "config_name = \"%s\")", section_name, config_name)

        logging.debug("Finish getting configuration value (value = \"%s\")",
                      value)

        return value

    def get_int(self, section_name, config_name, default_value=None):
        """
        Returns the configuration value of the setting in the specified section
        with the specified name in integer. If the setting is not available,
        returns the default value if not None, else throws RuntimeError.
        """

        logging.debug("Start getting integer configuration value "
                      "(section_name = \"%s\", config_name = \"%s\")",
                      section_name, config_name)

        value_string = self.get_value(section_name, config_name, default_value)

        try:
            value = int(value_string)
        except ValueError:
            logging.fatal(
                "Configuration value is not integer! (section_name = \"%s\", "
                "config_name = \"%s\", value = \"%s\")",
                section_name, config_name, value_string)
            raise RuntimeError()

        logging.debug("Finish getting integer configuration value "
                      "(value = %d)", value)

        return value

    def get_float(self, section_name, config_name, default_value=None):
        """
        Returns the configuration value of the setting in the specified section
        with the specified name in floating-point. If the setting is not
        available, returns the default value if not None, else throws
        RuntimeError.
        """

        logging.debug("Start getting floating-point configuration value "
                      "(section_name = \"%s\", config_name = \"%s\")",
                      section_name, config_name)

        value_string = self.get_value(section_name, config_name, default_value)

        try:
            value = float(value_string)
        except ValueError:
            logging.fatal(
                "Configuration value is not floating-point! (section_name = "
                "\"%s\", config_name = \"%s\", value = \"%s\")",
                section_name, config_name, value_string)
            raise RuntimeError()

        logging.debug("Finish getting floating-point configuration value "
                      "(value = %f)", value)

        return value
