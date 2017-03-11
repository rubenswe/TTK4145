"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import process_pairs
import core
import copy
import threading
import time


class ElevatorState(object):
    """
    State of elevator, including:
      - Position
      - Direction (going up/down, stopping)
      - Connected/disconnected
      - Serving requests from this floor
    To reduce complexity, all fields are public and directly accessible by
    the ElevatorMonitor class.
    """

    def __init__(self):
        self.position = 0
        self.direction = core.Direction.Stop
        self.is_connected = False
        self.serving_requests = list()


class ElevatorMonitorState(object):
    """
    Internal state of the elevator monitor module. For reducing complexity,
    all fields are public and directly accessible by the ElevatorMonitor class.
    """

    def __init__(self, elevator_number):

        self.elevator_list = [ElevatorState] * elevator_number

    def to_dict(self):
        """
        Returns the dictionary which contains the request manager state.
        """

        return {"elevator_list": copy.deepcopy(self.elevator_list)}

    def load_dict(self, data):
        """
        Imports the request manager state from the specified dictionary.
        """

        self.elevator_list = copy.deepcopy(data["elevator_list"])


class ElevatorMonitor(process_pairs.PrimaryBackupSwitchable):
    """
    Monitors the current state of all elevators, including:
      - Position
      - Direction (going up/down, stopping)
      - Connected/disconnected
      - Serving requests from this floor
    """

    def __init__(self, config):
        logging.debug("Start initializing elevator monitor")

        assert isinstance(config, core.Configuration)

        self.__elevator_number = config.get_int("core", "elevator_number")
        self.__period = config.get_float("floor", "elevator_monitor_period")

        logging.debug("Finish initializing elevator monitor")

    def start(self):
        """
        Starts working from the current state.
        """

        logging.debug("Start activating elevator monitor module")

        # Starts a new thread to periodically retrieve the current state
        # of all the elevators
        threading.Thread(
            target=self.__monitor_elevator_state_thread, daemon=True).start()

        logging.debug("Finish activating elevator monitor module")

    def __monitor_elevator_state_thread(self):

        logging.debug("Start elevator state monitoring thread")

        while True:

            time.sleep(self.__period)

        # Never end here
