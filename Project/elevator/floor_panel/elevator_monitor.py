"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import copy
import threading
import time
import process_pairs
import core
import transaction
import network


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
        self.serving_requests = set()


class ElevatorMonitorState(object):
    """
    Internal state of the elevator monitor module. For reducing complexity,
    all fields are public and directly accessible by the ElevatorMonitor class.
    """

    def __init__(self, elevator_number):

        self.elevator_list = [ElevatorState] * elevator_number

    def to_dict(self):
        """
        Returns the dictionary which contains the elevator monitor state.
        """

        return {"elevator_list": copy.deepcopy(self.elevator_list)}

    def load_dict(self, data):
        """
        Imports the elevator monitor state from the specified dictionary.
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

    def __init__(self, config, _network):
        logging.debug("Start initializing elevator monitor")

        assert isinstance(config, core.Configuration)
        assert isinstance(_network, network.Network)

        self.__network = _network

        self.__floor = config.get_int("floor", "floor")
        self.__elevator_number = config.get_int("core", "elevator_number")
        self.__period = config.get_float("floor", "elevator_monitor_period")
        self.__max_attempts = config.get_int(
            "floor", "elevator_monitor_attempts")

        self._state = ElevatorMonitorState(self.__elevator_number)

        self.__elevator_address = [
            (config.get_value("network", "elevator_%d.address" % (index)),
             config.get_int("network", "elevator_%d.port" % (index)))
            for index in range(self.__elevator_number)
        ]

        logging.debug("Finish initializing elevator monitor")

    def start(self):
        """
        Starts working from the current state.
        """

        logging.debug("Start activating elevator monitor module")

        # Starts new threads to periodically retrieve the current state
        # of all the elevators
        for index in range(self.__elevator_number):
            threading.Thread(target=self.__monitor_elevator_state_thread,
                             daemon=True,
                             args=(index,)).start()

        logging.debug("Finish activating elevator monitor module")

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of elevator monitor")
        data = self._state.to_dict()
        logging.debug("Finish exporting current state of elevator monitor")

        return data

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of elevator monitor")
        self._state.load_dict(state)
        logging.debug("Finish importing current state of elevator monitor")

    def __monitor_elevator_state_thread(self, index):
        """
        Monitors the specified elevator state.
        """

        logging.debug("Start elevator %d monitoring thread", index)

        attempts = 0
        address = self.__elevator_address[index]
        state = self._state.elevator_list[index]
        out_data = {"floor": self.__floor}

        while True:
            logging.debug("Ask elevator %d for its current state", index)

            attempts += 1
            new_state = self.__network.send_packet(
                address, "elev_state_get", out_data)

            if new_state is not False:
                logging.debug(
                    "Elevator %d current state: %s", index, new_state)

                state.is_connected = True
                attempts = 0

                state.position = new_state["position"]
                state.direction = new_state["direction"]
                state.serving_requests = new_state["serving_requests"]
            else:
                logging.error(
                    "Cannot get the state of elevator %d (attempt: %d)",
                    index, attempts)

                if attempts > self.__max_attempts:
                    state.is_connected = False

            time.sleep(self.__period)

        # Never end here
