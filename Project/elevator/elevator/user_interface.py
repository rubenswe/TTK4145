"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import process_pairs
import logging
import threading
import elevator_driver


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
        #
        """
         The elevator should be initialized with(Should all this be in the config?):
            - self.state # position and direction(UP=1, STOP=0, DOWN=-1)
            - self. counter #  for testing?
            - self.running #  not needed?
            - self.door_state
        """
        self.__lock_state = threading.Lock()
        self.__running = True
        self.state = dict()  # dictionary with default position and direction? Given by config?

        pass

    def start(self):
        """
        Starts working from the current state
        """
        logging.debug("Start activating user interface module")

        # print("Start elevator in current state: {}".format())
        # thread = threading.Thread()

        logging.debug("Finish activating user interface module")

    # Should have a function that listens for key presses in the elevator, should this be in the driver?

    # When a button in the elevator is pushed, call this function:
    def set_target_floor(self):
        # void elev_set_button_lamp(elev_button_type_t button, int floor, int value)
        pass

    # When an elevator reaches its destination, or gets a request, set the door light:
    def set_door_state(self):
        # void elev_set_door_open_lamp(int value) #  value is 0 or 1 (off/on)
        pass

    # When ...
    def set_elevator_state(self):
        pass

    # When the stop button is pressed, call this function:
    def stop(self):
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
