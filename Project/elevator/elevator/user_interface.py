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
import elevator.request_manager
import module_base


class UserInterface(module_base.ModuleBase):
    """
    Provides user interacting interface, including:
        - Target(Destination) floor(from 0 to 3)
        - Door open/closed light
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__started = False

        self.__floor = None
        self.__door_opened = False
        self.__curr_floor = 0

        self.__floor_number = None
        self.__period = 0.0

        self.__transaction_manager = None
        self.__driver = None

        self.__request_manager = None

    def init(self, config, transaction_manager, _driver, request_manager):
        """
        Initializes the user interface for the elevator panel
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)
        assert isinstance(request_manager,
                          elevator.request_manager.RequestManager)

        module_base.ModuleBase.init(self, transaction_manager)

        self.__transaction_manager = transaction_manager
        self.__driver = _driver
        self.__request_manager = request_manager

        self.__floor_number = config.get_int("core", "floor_number")
        self.__period = config.get_float("elevator", "ui_monitor_period")

        self.__floor = [0] * self.__floor_number

    def start(self, tid):
        """
        Starts working from the current state
        """

        self._join_transaction(tid)
        logging.debug("Start activating user interface module")

        self.__started = True

        # print("Start elevator in current state: {}".format())
        # Starts button monitoring thread
        logging.debug("Start button monitoring thread")
        threading.Thread(
            target=self.__button_monitor_thread, daemon=True).start()

        logging.debug("Finish activating user interface module")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of user interface")

        state = {
            "floor": self.__floor,
            "door_opened": self.__door_opened,
            "curr_floor": self.__curr_floor,
        }

        logging.debug("Finish exporting current state of user interface")
        return state

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of user interface")

        self.__floor = state["floor"]
        self.__door_opened = state["door_opened"]
        self.__curr_floor = state["curr_floor"]

        logging.debug("Finish importing current state of user interface")

    def turn_button_light_off(self, tid, floor):
        """
        Turns off the specified floor button light.
        """

        self._join_transaction(tid)
        logging.debug("Start turning the button light off (floor = %d)", floor)

        self.__floor[floor] = 0

        # Not turns off the light yet, wait for commit

        logging.debug("Finish turning the button light off (floor = %d)",
                      floor)

    def set_door_open_light(self, tid, is_opened):
        """
        Turns on/off the door indicator.
        """

        self._join_transaction(tid)
        self.__door_opened = is_opened

    def set_floor_indicator(self, tid, curr_floor):
        """
        Turns on the current floor.
        """

        self._join_transaction(tid)
        self.__curr_floor = curr_floor

    def prepare_to_commit(self, tid):
        """
        Before committing, updates the button lights to make sure that
        the button lights can only be changed when the transaction is success.
        """

        self._join_transaction(tid)
        if self._get_can_commit(tid):
            if self.__started:
                for floor in range(self.__floor_number):
                    self.__driver.set_button_lamp(
                        driver.FloorButton.Command, floor, self.__floor[floor])

        if self.__door_opened:
            self.__driver.set_door_open_lamp(1)
        else:
            self.__driver.set_door_open_lamp(0)

        self.__driver.set_floor_indicator(self.__curr_floor)

        return module_base.ModuleBase.prepare_to_commit(self, tid)

    def __button_monitor_thread(self):
        """
        Periodically checks whether a button is pushed.
        """

        logging.debug("Start monitoring elevator panel buttons")

        is_pushed = [0, 0, 0, 0]

        while True:

            # Checks each elevator panel button(0,1,2,3)
            # TODO: When any of the buttons is pushed, send a request to the
            # RequestManager
            for floor in range(len(is_pushed)):
                value = self.__driver.get_button_signal(2, floor)
                if is_pushed[floor] == 0 and value == 1:
                    # This button is pushed
                    logging.info("Button to floor %d is pushed", floor)

                    # Creates a new transaction and send the request
                    # to the request manager
                    tid = self.__transaction_manager.start()
                    self._join_transaction(tid)

                    self.__floor[floor] = 1
                    # Send a request to the RequestManager
                    logging.debug("Send request to the request manager")
                    self.__request_manager.add_cabin_request(tid, floor)

                    self.__transaction_manager.finish(tid)

                is_pushed[floor] = value
                # The button should light until the request has been served
                # self.__floor[floor] = value

            time.sleep(self.__period)
