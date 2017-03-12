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


class MotorController(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__driver = None

        self.__period = None

        self.__target_floor = 0
        self.__prev_floor = -1
        self.__direction = core.Direction.Stop

    def init(self, config, transaction_manager, _driver):
        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)

        module_base.ModuleBase.init(self, transaction_manager)

        self.__driver = _driver

        self.__period = config.get_float("elevator", "motor_controller_period")

    def start(self):
        threading.Thread(target=self.__control_motor_thread,
                         daemon=True).start()

    def export_state(self, tid):
        self._join_transaction(tid)
        state = {
            "target_floor": self.__target_floor,
            "prev_floor": self.__prev_floor,
            "direction": self.__direction,
        }

        return state

    def import_state(self, tid, state):
        self._join_transaction(tid)
        self.__target_floor = state["target_floor"]
        self.__prev_floor = state["prev_floor"]
        self.__direction = state["direction"]

    def set_target_floor(self, tid, target_floor):
        self._join_transaction(tid)
        self.__target_floor = target_floor

    def __control_motor_thread(self):
        self.__driver.set_motor_direction(driver.MotorDirection.Down)
        self.__direction = core.Direction.Down

        while True:
            self.__prev_floor = self.__driver.get_floor_sensor_signal()
            if self.__prev_floor != -1:
                break

        while True:
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

            if curr_position != -1:
                self.__prev_floor = curr_position

            time.sleep(self.__period)
