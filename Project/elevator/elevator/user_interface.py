"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import process_pairs
import logging
import json
import threading
# import elevator_driver #  not yet commited


class UserInterface(process_pairs.PrimaryBackupSwitchable):
    """
    Provides user interacting interface, including:
        - Start/Stop
        - Destination floor(from 0 to 3)
        - Door open/closed light
        - (Obstruction?)
    """

    def __init__(self, config):
        # What state should the elevators start in? -> Decided by the config
        # ...
        """
         The elevator should be initialized with(Should all this be in the config?):
            - self.state
            - self. counter #  for testing?
            -self.running #  not needed?
        """
        self.__lock_state = threading.Lock()

        pass

    def start(self):
        """
        Starts working from the current state
        """
        logging.debug("Start activating user interface module")

        # print("Start elevator in current state: {}".format())

        logging.debug("Finish activating user interface module")

    def get_target_floor(self):
        pass

    def

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of user interface")

        state = dict()

        logging.debug("Finish exporting current state of user interface")
        return state

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of user interface")
        logging.debug("Finish importing current state of user interface")
