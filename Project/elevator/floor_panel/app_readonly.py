"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import argparse
import time
import core
import network
import process_pairs
import transaction
import driver
import module_base
import threading

logging.basicConfig(format="%(process)d | %(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class FloorReadonly(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__transaction_manager = None
        self.__network = None
        self.__driver = None

        self.__period = None
        self.__floor_number = None
        self.__floor_address = None

    def init(self, config, transaction_manager, _network, _driver):

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(_driver, driver.Driver)

        module_base.ModuleBase.init(self, transaction_manager)

        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__driver = _driver

        self.__period = config.get_float("floor", "readonly_period")
        self.__floor_number = config.get_int("core", "floor_number")
        self.__floor_address = [
            (config.get_value("network", "floor_%d.ip_address" % (index)),
             config.get_int("network", "floor_%d.port" % (index)))
            for index in range(self.__floor_number)
        ]

    def start(self):
        threading.Thread(target=self.__show_floor_button_light_thread,
                         daemon=True).start()

    def export_state(self, tid):
        self._join_transaction(tid)
        return dict()

    def import_state(self, tid, state):
        self._join_transaction(tid)

    def __show_floor_button_light_thread(self):
        while True:
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            for floor in range(self.__floor_number):
                resp = self.__network.send_packet(
                    self.__floor_address[floor],
                    "floor_get_all_requests",
                    True)

                if resp is not False:
                    call_up, call_down = resp
                    if call_up:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallUp, floor, 1)
                    else:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallUp, floor, 0)

                    if call_down:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallDown, floor, 1)
                    else:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallDown, floor, 0)

            self.__transaction_manager.finish(tid)

            time.sleep(self.__period)


def main():
    """
    Starts running
    """

    # Arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode", type=str, default="primary",
        help="Process pairs mode (primary/backup). Default: primary")

    args = parser.parse_args()

    # Initializes modules
    node_name = "floor_readonly"

    config = core.Configuration("../config/local-test.conf", node_name)
    transaction_manager = transaction.TransactionManager()

    _network = network.Network()
    _driver = driver.Driver()
    floor_readonly = FloorReadonly()

    _network.init(config, transaction_manager)
    _driver.init(config, transaction_manager)
    floor_readonly.init(config, transaction_manager, _network, _driver)

    module_list = {
        "network": _network,
        "driver": _driver,
        "floor_readonly": floor_readonly,
    }

    # Starts
    pair = process_pairs.ProcessPair()
    pair.init(config, transaction_manager, args)
    pair.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
