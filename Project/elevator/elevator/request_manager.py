"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import module_base
import core
import transaction
import network
import elevator
import threading
import enum
import time


class RequestTableRow(object):
    """
    Data structure of the requests
    """

    def __init__(self):
        self.call_up = False
        self.call_down = False
        self.cabin = False


class ElevatorState(enum.IntEnum):
    Stop = 0,
    Stay = 1,
    Move = 2


class RequestManager(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__transaction_manager = None
        self.__network = None
        self.__motor_controller = None
        self.__user_interface = None

        self.__elevator = None
        self.__floor_number = None
        self.__period = None
        self.__stay_time = None
        self.__floor_address = None

        # State
        self.__request_floors = None

    def init(self, config, transaction_manager, _network,
             motor_controller, user_interface):
        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(motor_controller,
                          elevator.motor_controller.MotorController)
        assert isinstance(user_interface,
                          elevator.user_interface.UserInterface)

        module_base.ModuleBase.init(self, transaction_manager)

        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__motor_controller = motor_controller
        self.__user_interface = user_interface

        self.__elevator = config.get_int("elevator", "elevator")
        self.__floor_number = config.get_int("core", "floor_number")
        self.__period = config.get_float("elevator", "elevator_control_period")
        self.__stay_time = config.get_float("elevator", "stay_time")
        self.__floor_address = [
            (config.get_value("network", "floor_%d.ip_address" % (index)),
             config.get_int("network", "floor_%d.port" % (index)))
            for index in range(self.__floor_number)
        ]

        # State
        self.__request_floors = [
            RequestTableRow() for i in range(self.__floor_number)
        ]

        # Registers imcoming packet handler
        _network.add_packet_handler("elev_request_add",
                                    self.__on_elev_request_add_received)

    def start(self, tid):
        self._join_transaction(tid)

    def export_state(self, tid):
        self._join_transaction(tid)
        state = {
            "request_floors": self.__request_floors,
        }
        return state

    def import_state(self, tid, state):
        self._join_transaction(tid)
        self.__request_floors = state["request_floors"]

    def add_cabin_request(self, tid, floor):

        self._join_transaction(tid)
        logging.info("Add cabin request to floor %d", floor)
        self.__request_floors[floor].cabin = True

    def __on_elev_request_add_received(self, tid, address, data):
        self._join_transaction(tid)

        floor = data["floor"]
        direction = data["direction"]

        logging.info("Add floor request (floor = %d, direction = %s)",
                     floor, direction)

        if direction == core.Direction.Up:
            self.__request_floors[floor].call_up = True
        else:
            self.__request_floors[floor].call_down = True

        return True

    def get_current_request_list(self, tid):
        """
        Returns the current list of all requests.
        """

        self._join_transaction(tid)
        logging.debug("Start returning the current request list")

        logging.debug("Finish returning the current request list")
        return self.__request_floors

    def set_request_served(self, tid, floor, direction):
        self._join_transaction(tid)

        # Removes the request belongs to this floor and turns off the light
        if direction == core.Direction.Up:
            self.__request_floors[floor].call_up = False
        if direction == core.Direction.Down:
            self.__request_floors[
                floor].call_down = False

        if self.__request_floors[floor].cabin:
            self.__request_floors[floor].cabin = False
            self.__user_interface.turn_button_light_off(
                tid, floor)

        # Sends request served message to the floor panel
        self.__network.send_packet(
            self.__floor_address[floor],
            "floor_request_served",
            {"elevator": self.__elevator, "direction": direction})
