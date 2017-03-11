"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import copy
import process_pairs
import transaction
import network
import core
import floor_panel.user_interface


class RequestManagerState(object):
    """
    Internal state of the request manager module. For reducing complexity,
    all fields are public and directly accessible by the RequestManager class.
    """

    def __init__(self):
        # Up/down request is waiting to be served
        self.has_request = {
            core.Direction.Up: False,
            core.Direction.Down: False,
        }

        # Elevator which is serving the request
        self.serving_elevator = {
            core.Direction.Up: -1,
            core.Direction.Down: -1,
        }

    def to_dict(self):
        """
        Returns the dictionary which contains the request manager state.
        """

        return {
            "has_request": copy.deepcopy(self.has_request),
            "serving_elevator": copy.deepcopy(self.serving_elevator),
        }

    def load_dict(self, data):
        """
        Imports the request manager state from the specified dictionary.
        """

        self.has_request = copy.deepcopy(data["has_request"])
        self.serving_elevator = copy.deepcopy(data["serving_elevator"])


class RequestManager(process_pairs.PrimaryBackupSwitchable,
                     transaction.ResourceManager):
    """
    Receives user request from the user interface and sends to the appropriate
    elevator.
    """

    def __init__(self, config, transaction_manager, _network):
        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)

        transaction.ResourceManager.__init__(self, transaction_manager)

        self.__config = config
        self.__floor = config.get_int("floor", "floor")

        self.__transaction_manager = transaction_manager
        self.__network = _network

        self.__user_interface = None

        self._state = RequestManagerState()
        self.__prev_state = RequestManagerState()
        self.__can_commit = True

        _network.add_packet_handler("floor_request_served",
                                    self.__on_request_served_received)

    def init(self, user_interface):
        assert isinstance(user_interface,
                          floor_panel.user_interface.UserInterface)

        self.__user_interface = user_interface

    def start(self):
        """
        Starts working from the current state.
        """

        logging.debug("Start activating request manager module")

        logging.debug("Finish activating request manager module")

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of request manager")
        data = self._state.to_dict()
        logging.debug("Finish exporting current state of request manager")

        return data

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of request manager")
        self._state.load_dict(state)
        logging.debug("Finish importing current state of request manager")

    def prepare_to_commit(self, tid):
        """
        Returns whether the specified transaction is ok or not.
        """

        self.join_transaction(tid)
        return self.__can_commit

    def commit(self, tid):
        """
        Keeps the new state of the module and unlocks the resources.
        """

        self.join_transaction(tid)
        logging.debug("Start committing the transaction (tid = %s)", tid)

        self.__prev_state = copy.deepcopy(self._state)
        self.__can_commit = True

        logging.debug("Finish commit the transaction (tid = %s)", tid)
        self.leave_transaction(tid)

    def abort(self, tid):
        """
        Restores the previous state of the module and unlocks the resources.
        """

        self.join_transaction(tid)
        logging.debug("Start aborting the transaction (tid = %s)", tid)

        self._state = copy.deepcopy(self.__prev_state)
        self.__can_commit = True

        logging.debug("Finish aborting the transaction (tid = %s)", tid)
        self.leave_transaction(tid)

    def add_request(self, tid, direction):
        """
        Adds a new request from users. After determining the appropriate
        elevator, the request will be sent to that elevator.
        """

        assert isinstance(direction, core.Direction)

        self.join_transaction(tid)
        logging.debug("Start adding new request (tid = %s, direction = %s)",
                      tid, direction)

        state = self._state

        if not state.has_request[direction]:
            # Adds new request
            state.has_request[direction] = True

            # Finds the appropriate elevator
            elev_no = 0
            elev_address = (
                self.__config.get_value("network", "elevator_0.address"),
                self.__config.get_int("network", "elevator_0.port"))

            # Sends request to the appropriate elevator
            data = {
                "floor": self.__floor,
                "direction": direction,
            }

            logging.debug(
                "Send the request to elevator %d (addr = %s, data = %s)",
                elev_no, elev_address, data)

            resp = self.__network.send_packet(
                elev_address, "elev_request_add", data)

            if resp is not True:
                logging.error(
                    "Cannot send the request to elevator %d", elev_no)
                self.__can_commit = False
            else:
                logging.info("Request has been sent to elevator "
                             "(direction = %d, elevator = %d)",
                             direction, elev_no)

                state.serving_elevator[direction] = elev_no

        logging.debug("Finish adding new request (tid = %s, direction = %s)",
                      tid, direction)

        return self.__can_commit

    def __on_request_served_received(self, tid, address, data):

        self.join_transaction(tid)
        logging.debug("Start handling request served packet from elevator")

        # Extracts the served elevator and direction
        elevator = data["elevator"]
        direction = data["direction"]

        # Removes the request from pending request list
        self._state.has_request[direction] = False

        # Turns off the button light

        logging.info("Request has been served (direction = %d, elevator = %d)",
                     direction, elevator)

        logging.debug("Finish handling request served packet from elevator")

        return True
