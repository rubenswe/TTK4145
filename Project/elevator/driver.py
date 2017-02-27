"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import ctypes
import enum
import logging
import process_pairs


class DriverTarget(enum.IntEnum):

    Comedi = 0,
    Simulation = 1


class Driver(process_pairs.PrimaryBackupSwitchable):
    """
    Provides functionalities to interact with hardware components, including:
        - Floor panels buttons and lights
        - An elevator panel buttons and lights
        - An elevator motor and sensors
    """

    def __init__(self, config):

        # Gets the driver target (hardware or simulation)
        self.__type = DriverTarget.Simulation
        if config.get_value("driver", "type") == "Comedi":
            self.__type = DriverTarget.Comedi

        # If it is simulation, address of the simulator is needed
        if self.__type == DriverTarget.Simulation:
            self.__address = (
                config.get_value("driver", "ip_address"),
                config.get_value("driver", "port"))
        else:
            self.__address = ("", "")

        # C driver library
        self.__lib = ctypes.cdll.LoadLibrary(
            "../driver/libdriver.so")

        """self.__lib.elev_init.argtypes = [ctypes.c_int,
                                         ctypes.POINTER(ctypes.c_char),
                                         ctypes.POINTER(ctypes.c_char)]
        self.__lib.elev_set_motor_direction.argtypes = [ctypes.c_int]
        self.__lib.elev_set_button_lamp.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.__lib.elev_set_floor_indicator.argtypes = [ctypes.c_int]
        self.__lib.elev_set_door_open_lamp.argtypes = [ctypes.c_int]
        self.__lib.elev_set_stop_lamp.argtypes = [ctypes.c_int]
        self.__lib.elev_get_button_signal.argtypes = [
            ctypes.c_int, ctypes.c_int]
        self.__lib.elev_get_button_signal.restype = ctypes.c_int
        self.__lib.elev_get_floor_sensor_signal.restype = ctypes.c_int
        self.__lib.elev_get_stop_signal.restype = ctypes.c_int
        self.__lib.elev_get_obstruction_signal.restype = ctypes.c_int"""

            
    def start(self):
        """
        Starts working from the current state.
        """

        logging.debug("Start activating driver module")
        
        self.__lib.elev_init(self.__type, self.__address[0], self.__address[1])
        
        logging.debug("Finish activating driver module")

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of driver")
        logging.debug("Finish exporting current state of driver")
        return dict()

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of driver")
        logging.debug("Finish importing current state of driver")

    def set_motor_direction(self, direction):
        self.__lib.elev_set_motor_direction(direction)

    def set_button_lamp(self, button, floor, value):
        self.__lib.elev_set_button_lamp(button, floor, value)

    def set_floor_indicator(self, floor):
        self.__lib.elev_set_floor_indicator(floor)

    def set_door_open_lamp(self, value):
        self.__lib.elev_set_door_open_lamp(value)

    def set_stop_lamp(self, value):
        self.__lib.elev_set_stop_lamp(value)

    def get_button_signal(self, button, floor):
        return self.__lib.elev_get_button_signal(button, floor)

    def get_floor_sensor_signal(self):
        return self.__lib.elev_get_floor_sensor_signal()

    def get_stop_signal(self):
        return self.__lib.elev_get_stop_signal()

    def get_obstruction_signal(self):
        return self.__lib.elev_get_obstruction_signal()
