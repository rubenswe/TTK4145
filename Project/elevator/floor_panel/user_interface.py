"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import threading
import process_pairs
import driver
import time
import core
import transaction


class UserInterfaceState(object):
    """
    Internal state of the user interface module. For reducing complexity,
    all fields are public and directly accessible by the UserInterface class.
    """

    def __init__(self):
        self.light_up = False  # Whether the up button light is on
        self.light_down = False  # Whether the down button light is on

    def to_dict(self):
        """
        Returns the dictionary which contains the user interface state.
        """

        return {
            "light_up": self.light_up,
            "light_down": self.light_down
        }

    def load_dict(self, data):
        """
        Imports the user interface state from the specified dictionary.
        """

        self.light_up = data["light_up"]
        self.light_down = data["light_down"]


class UserInterface(process_pairs.PrimaryBackupSwitchable):
    """
    Provides user interacting interface, including:
        - Up/Down button
        - Up/Down light
    """

    def __init__(self):
        self.__curr_state = UserInterfaceState()
        self.__prev_state = None

        self.__floor = 0
        self.__period = 0.0

        self.__transaction_manager = None
        self.__driver = None

    def init(self, config, _transaction_manager, _driver):
        """
        Initializes the user interface for floor panel
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(_transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)

        self.__floor = config.get_int("floor", "floor")
        self.__period = config.get_float("floor", "period", 0.1)

        self.__transaction_manager = _transaction_manager
        self.__driver = _driver

    def start(self):
        """
        Starts working from the current state.
        """

        logging.debug("Start activating user interface module")

        # Starts button monitoring thread
        logging.debug("Start button monitoring thread")
        threading.Thread(
            target=self.__button_monitor_thread, daemon=True).start()

        logging.debug("Finish activating user interface module")

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of user interface")

        data = self.__curr_state.to_dict()

        logging.debug("Finish exporting current state of user interface")
        return data

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of user interface")

        self.__curr_state.load_dict(state)

        logging.debug("Finish importing current state of user interface")

    def __button_monitor_thread(self):
        """
        Periodically checks whether button is pushed.
        """

        logging.debug("Start monitoring floor panel button")

        is_pushed = {
            driver.FloorButton.CallUp: 0,
            driver.FloorButton.CallDown: 0,
            driver.FloorButton.Command: 0,
        }

        while True:

            # Checks each button (up, down, command). If any of them is pushed,
            # sends request to the request manager
            for button in is_pushed:
                value = self.__driver.get_button_signal(button, self.__floor)
                if is_pushed[button] == 0 and value == 1:
                    # This button is pushed
                    logging.debug("Floor %d, button %d is pushed",
                                  self.__floor, button)

                is_pushed[button] = value

            time.sleep(self.__period)

        # This function never end
