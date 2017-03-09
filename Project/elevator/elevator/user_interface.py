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


class UserInterface(process_pairs.PrimaryBackupSwitchable):
    """
    Provides user interacting interface, including:
        - Start/Stop(not needed)
        - Target(Destination) floor(from 0 to 3)
        - Door open/closed light
        - Obstruction(not needed)
    """

    def __init__(self, config):
        """
         The elevator should be initialized with:
            - self.state # position and direction(UP=1, STOP=0, DOWN=-1)
            - self. counter #  for testing?
            - self.running #  not needed?
            - self.door_state
        """
        self.__lock_state = threading.Lock()
        self.__driver = driver.Driver(config)
        self.__target_floor = 0

        pass

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

    # Not needed?:
    def set_elevator_state(self):
        pass

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of user interface")

        self.__lock_state.acquire()
        state = {
            "type": self.state,  # elevator_state?
            "data": None
        }
        self.__lock_state.release()

        logging.debug("Finish exporting current state of user interface")
        return state

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
                is_pushed[floor] = value
