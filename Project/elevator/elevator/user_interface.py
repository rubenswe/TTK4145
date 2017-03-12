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
import elevator
from elevator import request_manager


class UserInterFaceState(object):
    """
    Internal state of the user interface module. For reducing complexity,
    all fields are public and directly accessible by the UserInterface class.
    """

    def __init__(self):
        self.floor = [0, 0, 0, 0]
        self.light_door = False

    def to_dict(self):
        """
        Returns the dictionary which contains the user interface state.
        """

        return {
            "light_floor": self.floor,
            "light_door": self.light_door
        }

    def load_dict(self, data):
        """
        Imports the user interface state from the specified dictionary
        """
        self.floor = data["light_floor"]
        self.light_door = data["light_door"]


class UserInterface(process_pairs.PrimaryBackupSwitchable):
    """
    Provides user interacting interface, including:
        - Target(Destination) floor(from 0 to 3)
        - Door open/closed light
    """

    def __init__(self):
        self.curr_state = UserInterFaceState()
        self.prev_state = None

        self.__floor = [0, 0, 0, 0]
        self.__period = 0.0

        self.__transaction_manager = None
        self.__driver = None

        self.__request_manager = None
        # self.__lock_state = threading.Lock()

    def init(self, config, _driver, _request_manager):
        """
        Initializes the user interface for the elevator panel
        """

        assert isinstance(config, core.Configuration)
        # assert isinstance(_transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)
        # assert isinstance(request_manager, elevator.request_manager.RequestManager)

        self.__driver = _driver
        self.__request_manager = _request_manager

    def start(self):
        """
        Starts working from the current state
        """
        logging.debug("Start activating user interface module")

        # print("Start elevator in current state: {}".format())
        # Starts button monitoring thread
        logging.debug("Start button monitoring thread")
        threading.Thread(target=self.__button_monitor_thread, daemon=True).start()

        logging.debug("Finish activating user interface module")

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of user interface")

        # self.__lock_state.acquire()
        # state = {
        #     "type": self.state,
        #     "data": None
        # }
        # self.__lock_state.release()

        logging.debug("Finish exporting current state of user interface")
        # return state

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of user interface")
        logging.debug("Finish importing current state of user interface")

    def __button_monitor_thread(self):
        """
        Periodically checks whether a button is pushed.
        """

        logging.debug("Start monitoring elevator panel buttons")

        is_pushed = [0, 0, 0, 0]

        while True:

            # Checks each elevator panel button(0,1,2,3)
            # TODO: When any of the buttons is pushed, send a request to the RequestManager
            for floor in range(len(is_pushed)):
                value = self.__driver.get_button_signal(2, floor)
                if is_pushed[floor] == 0 and value == 1:
                    # This button is pushed
                    logging.debug("ELEVATOR PANEL: Button to floor {} is pushed".format(floor+1))
                    # Send a request to the RequestManager
                    logging.debug("ELEVATOR PANEL: Send request to the request manager")
                    self.__request_manager.add_request(floor)

                is_pushed[floor] = value
                # The button should light until the request has been served
                # self.__floor[floor] = value
