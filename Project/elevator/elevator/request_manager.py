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

        self.__curr_position = 0
        self.__curr_motor_direction = core.Direction.Stop

        self.__curr_direction = core.Direction.Stop
        self.__curr_state = ElevatorState.Stop

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
        _network.add_packet_handler("elev_state_get",
                                    self.__on_elev_state_get_received)

    def start(self):
        pass

    def export_state(self, tid):
        self._join_transaction(tid)
        state = {
            "request_floors": self.__request_floors,
            "curr_position": self.__curr_position,
            "curr_motor_direction": self.__curr_motor_direction,
            "curr_direction": self.__curr_direction,
            "curr_state": self.__curr_state,
        }
        return state

    def import_state(self, tid, state):
        self._join_transaction(tid)
        self.__request_floors = state["request_floors"]
        self.__curr_motor_direction = state["curr_motor_direction"]
        self.__curr_position = state["curr_position"]
        self.__curr_direction = state["curr_direction"]
        self.__curr_state = state["curr_state"]

    def add_cabin_request(self, tid, floor):

        self._join_transaction(tid)
        logging.info("Add cabin request to floor %d", floor)
        self.__request_floors[floor].cabin = True

        self.__on_request_added(tid)

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

        self.__on_request_added(tid)

        return True

    def __on_elev_state_get_received(self, tid, address, data):
        self._join_transaction(tid)

        floor = data["floor"]

        # Gets list of requests belongs to that floor
        serving_requests = list()
        if self.__request_floors[floor].call_up:
            serving_requests.append(core.Direction.Up)
        if self.__request_floors[floor].call_down:
            serving_requests.append(core.Direction.Down)

        # Sends back the state
        return {
            "position": self.__curr_position,
            "direction": self.__curr_direction,
            "serving_requests": serving_requests
        }

    def __send_request_served(self, tid, floor, direction):
        self._join_transaction(tid)

        # Removes the request belongs to this floor and turns off the light
        if self.__curr_direction == core.Direction.Up:
            self.__request_floors[self.__curr_position].call_up = False
        if self.__curr_direction == core.Direction.Down:
            self.__request_floors[
                self.__curr_position].call_down = False

        if self.__request_floors[self.__curr_position].cabin:
            self.__request_floors[self.__curr_position].cabin = False
            self.__user_interface.turn_button_light_off(
                tid, self.__curr_position)

        # Sends request served message to the floor panel
        self.__network.send_packet(
            self.__floor_address[self.__curr_position],
            "floor_request_served",
            {"elevator": self.__elevator, "direction": self.__curr_direction})

    def on_position_and_motor_direction_changed(
            self, tid, position, direction):

        self._join_transaction(tid)
        logging.debug(
            "Start handling position and motor direction changed event "
            "(position = %d, direction = %s)",
            position, direction)

        self.__curr_position = position
        self.__curr_motor_direction = direction

        if self.__curr_state == ElevatorState.Move and \
                direction == core.Direction.Stop:
            # The elevator has reached the destination floor
            logging.info("Elevator has reached the floor %d",
                         self.__curr_position)

            self.__curr_state = ElevatorState.Stay

            self.__send_request_served(
                tid, self.__curr_position, self.__curr_direction)

            # Waits for a second before closing the door
            threading.Timer(self.__stay_time,
                            self.__elevator_stay_timer).start()

        logging.debug(
            "Finish handling position and motor direction changed event "
            "(position = %d, direction = %s)",
            position, direction)

    def __elevator_stay_timer(self):
        tid = self.__transaction_manager.start()
        self._join_transaction(tid)

        self.__send_request_served(
            tid, self.__curr_position, self.__curr_direction)

        next_destination = self.__find_next_destination(tid)
        if next_destination is not None:
            self.__motor_controller.set_target_floor(tid, next_destination)
            self.__curr_state = ElevatorState.Move
        else:
            # Tries to change the direction
            if self.__curr_direction == core.Direction.Up:
                self.__curr_direction = core.Direction.Down
            else:
                self.__curr_direction = core.Direction.Up

            next_destination = self.__find_next_destination(tid)

            if next_destination is not None:
                self.__motor_controller.set_target_floor(
                    tid, next_destination)
                self.__curr_state = ElevatorState.Move
            else:
                self.__curr_direction = ElevatorState.Stop
                self.__curr_state = ElevatorState.Stop

        self.__transaction_manager.finish(tid)

    def __on_request_added(self, tid):
        self._join_transaction(tid)

        if self.__curr_state == ElevatorState.Stop or \
                self.__curr_state == ElevatorState.Move:
            next_destination = self.__find_next_destination(tid)
            if next_destination is not None:
                self.__curr_state = ElevatorState.Move
                if self.__curr_direction == core.Direction.Stop:
                    if next_destination > self.__curr_position:
                        self.__curr_direction = core.Direction.Up
                    else:
                        self.__curr_direction = core.Direction.Down

                self.__motor_controller.set_target_floor(tid, next_destination)

    def __find_next_destination(self, tid):
        self._join_transaction(tid)

        next_destination = None
        ignore_curr_floor = 1
        if self.__curr_state != ElevatorState.Move:
            ignore_curr_floor = 0

        logging.info("Find next destination: %s", self.__request_floors)

        if self.__curr_direction == core.Direction.Up \
                or self.__curr_direction == core.Direction.Stop:

            # Looks up for the nearest request
            for floor in range(self.__curr_position + ignore_curr_floor,
                               self.__floor_number):
                if self.__request_floors[floor].call_up \
                        or self.__request_floors[floor].cabin:
                    next_destination = floor
                    break

            if next_destination is None:
                # Looks up for the farthest "down" request
                for floor in reversed(range(
                        self.__curr_position + ignore_curr_floor,
                        self.__floor_number)):
                    if self.__request_floors[floor].call_down:
                        next_destination = floor
                        break

        if self.__curr_direction == core.Direction.Down \
                or self.__curr_direction == core.Direction.Stop:
            # Looks down for the nearest request
            for floor in reversed(range(
                    0, self.__curr_position + ignore_curr_floor)):
                if self.__request_floors[floor].call_down \
                        or self.__request_floors[floor].cabin:
                    next_destination = floor
                    break

            if next_destination is None:
                # Looks down for the farthest "up" request
                for floor in range(
                        0, self.__curr_position + ignore_curr_floor):
                    if self.__request_floors[floor].call_up:
                        next_destination = floor
                        break

        return next_destination
