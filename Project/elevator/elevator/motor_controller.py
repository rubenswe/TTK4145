"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import module_base
import transaction
import driver
import threading
import core
import time
import elevator


class MotorController(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__driver = None

        # Configurations
        self.__period = None
        self.__stuck_timeout = None

        # States
        self.__target_floor = 0
        self.__prev_floor = -1
        self.__direction = core.Direction.Stop
        self.__stuck_counter = 0
        self.__is_stuck = False

    def init(self, config, transaction_manager, _driver):
        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)

        module_base.ModuleBase.init(self, transaction_manager)

        self.__transaction_manager = transaction_manager
        self.__driver = _driver

        self.__period = config.get_float("elevator", "motor_controller_period")
        self.__stuck_timeout = config.get_float(
            "elevator", "motor_stuck_timeout")

    def start(self, tid):
        self._join_transaction(tid)
        threading.Thread(target=self.__control_motor_thread,
                         daemon=True).start()

    def export_state(self, tid):
        self._join_transaction(tid)
        state = {
            "target_floor": self.__target_floor,
            "prev_floor": self.__prev_floor,
            "direction": self.__direction,
            "stuck_counter": self.__stuck_counter,
            "is_stuck": self.__is_stuck,
        }

        return state

    def import_state(self, tid, state):
        self._join_transaction(tid)
        self.__target_floor = state["target_floor"]
        self.__prev_floor = state["prev_floor"]
        self.__direction = state["direction"]
        self.__stuck_counter = state["stuck_counter"]
        self.__is_stuck = state["is_stuck"]

    def get_current_position_direction(self, tid):
        self._join_transaction(tid)
        return self.__prev_floor, self.__direction

    def set_target_floor(self, tid, target_floor):
        self._join_transaction(tid)
        self.__target_floor = target_floor

    def is_stuck(self, tid):
        self._join_transaction(tid)
        return self.__is_stuck

    def __control_motor_thread(self):

        prev_position = -1

        tid = self.__transaction_manager.start()
        self._join_transaction(tid)

        if self.__prev_floor == -1:
            self.__driver.set_motor_direction(driver.MotorDirection.Down)
            self.__direction = core.Direction.Down

            while True:
                self.__prev_floor = self.__driver.get_floor_sensor_signal()
                if self.__prev_floor != -1:
                    break

        self.__transaction_manager.finish(tid)

        while True:
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            if self.__prev_floor < self.__target_floor:
                if self.__direction != core.Direction.Up:
                    self.__driver.set_motor_direction(driver.MotorDirection.Up)
                    self.__direction = core.Direction.Up
            elif self.__prev_floor > self.__target_floor:
                if self.__direction != core.Direction.Down:
                    self.__driver.set_motor_direction(
                        driver.MotorDirection.Down)
                    self.__direction = core.Direction.Down

            curr_position = self.__driver.get_floor_sensor_signal()
            if curr_position == self.__target_floor:
                if self.__direction != core.Direction.Stop:
                    self.__driver.set_motor_direction(
                        driver.MotorDirection.Stop)
                    self.__direction = core.Direction.Stop

            # Determines whether the motor is still running or not
            if self.__direction == core.Direction.Stop:
                self.__stuck_counter = 0
                self.__is_stuck = False
            else:
                if curr_position == prev_position:
                    if self.__period * self.__stuck_counter > \
                            self.__stuck_timeout:
                        # Timeout => The motor cannot move
                        logging.error("The motor cannot move!")
                        self.__is_stuck = True

                    self.__stuck_counter += 1
                else:
                    self.__stuck_counter = 0
                    self.__is_stuck = False

            if curr_position != -1:
                self.__prev_floor = curr_position

            _ = self.__transaction_manager.finish(tid)

            time.sleep(self.__period)
