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

        self.__floor = [0, 0, 0, 0]
        self.__period = 0.0

        self.__transaction_manager = None
        self.__driver = None

        self.__request_manager = None
        # self.__lock_state = threading.Lock()

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

        self.__period = config.get_float("elevator", "ui_monitor_period")

    def start(self):
        """
        Starts working from the current state
        """
        logging.debug("Start activating user interface module")

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

        logging.debug("Finish importing current state of user interface")

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
                    logging.info(
                        "ELEVATOR PANEL: Button to floor %d is pushed",
                        floor + 1)

                    # Creates a new transaction and send the request
                    # to the request manager
                    tid = self.__transaction_manager.start()
                    self._join_transaction(tid)

                    self.__floor[floor] = 1
                    # Send a request to the RequestManager
                    logging.debug(
                        "ELEVATOR PANEL: Send request to the request manager")
                    self.__request_manager.add_cabin_request(tid, floor)

                    self.__transaction_manager.finish(tid)

                is_pushed[floor] = value
                # The button should light until the request has been served
                # self.__floor[floor] = value

            time.sleep(self.__period)
