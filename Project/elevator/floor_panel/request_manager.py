"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import transaction
import network
import core
import floor_panel.user_interface
import module_base


class RequestManager(module_base.ModuleBase):
    """
    Receives user request from the user interface and sends to the appropriate
    elevator.
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__config = None
        self.__transaction_manager = None
        self.__network = None
        self.__user_interface = None

        # Configurations
        self.__floor = None

        # Up/down request is waiting to be served
        self.__has_request = {
            core.Direction.Up: False,
            core.Direction.Down: False,
        }

        # Elevator which is serving the request
        self.__serving_elevator = {
            core.Direction.Up: -1,
            core.Direction.Down: -1,
        }

    def init(self, config, transaction_manager, _network, user_interface):
        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(user_interface,
                          floor_panel.user_interface.UserInterface)

        module_base.ModuleBase.init(self, transaction_manager)

        self.__config = config
        self.__floor = config.get_int("floor", "floor")
        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__user_interface = user_interface

        # Registers incoming packet handlers
        _network.add_packet_handler("floor_request_served",
                                    self.__on_request_served_received)

    def start(self):
        """
        Starts working from the current state.
        """

        logging.debug("Start activating request manager module")

        logging.debug("Finish activating request manager module")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of request manager")

        data = {
            "has_request": self.__has_request,
            "serving_elevator": self.__serving_elevator,
        }

        logging.debug("Finish exporting current state of request manager")

        return data

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of request manager")

        self.__has_request = state["has_request"]
        self.__serving_elevator = state["serving_elevator"]

        logging.debug("Finish importing current state of request manager")

    def add_request(self, tid, direction):
        """
        Adds a new request from users. After determining the appropriate
        elevator, the request will be sent to that elevator.
        """

        assert isinstance(direction, core.Direction)

        self._join_transaction(tid)
        logging.debug("Start adding new request (tid = %s, direction = %s)",
                      tid, direction)

        if not self.__has_request[direction]:
            # Adds new request
            self.__has_request[direction] = True

            # Finds the appropriate elevator
            elev_no = 0
            elev_address = (
                self.__config.get_value("network", "elevator_0.ip_address"),
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
                self._set_can_commit(tid, False)

                return False
            else:
                logging.info("Request has been sent to elevator "
                             "(direction = %d, elevator = %d)",
                             direction, elev_no)

                self.__serving_elevator[direction] = elev_no

        logging.debug("Finish adding new request (tid = %s, direction = %s)",
                      tid, direction)

        return True

    def __on_request_served_received(self, tid, address, data):

        self._join_transaction(tid)
        logging.debug("Start handling request served packet from elevator")

        # Extracts the served elevator and direction
        elevator = data["elevator"]
        direction = data["direction"]

        # Removes the request from pending request list
        self.__has_request[direction] = False

        # Turns off the button light

        logging.info("Request has been served (direction = %d, elevator = %d)",
                     direction, elevator)

        logging.debug("Finish handling request served packet from elevator")

        return True
