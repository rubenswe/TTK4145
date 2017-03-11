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
from elevator import user_interface
from elevator import request_manager

logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                           " (%(module)s.%(funcName)s)",
                    level=logging.DEBUG)


def main():

    # Arguments
    parser = argparse.ArgumentParser()

    # parser.add_argument("elevator", type=int, help="Elevator number (Elevator 0 is the first elevator)")
    parser.add_argument("--mode", type=str, default="primary",
                        help="Process pairs mode (primary/backup). Default: primary")

    args = parser.parse_args()

    # Initialize modules
    node_name = "elevator_{}".format(0)

    config = core.Configuration("../config/local-test.conf", node_name)
    net = network.Network(config)
    transaction_manager = transaction.TransactionManager()
    _user_interface = user_interface.UserInterface()
    _driver = driver.Driver(config)
    _request_manager = request_manager.RequestManager(config, net)
    _user_interface.init(config, _driver, _request_manager)

    module_list = {
        "network": net,
        "driver": _driver,
        "user_interface": _user_interface,
        "request_manager": _request_manager
    }

    # Starts
    pair = process_pairs.ProcessPair(config, args)
    pair.start(module_list)

    while True:
        #  Wait for commands from the elevator panel

        if _driver.get_button_signal(2, 1):
            _driver.set_button_lamp(2, 1, 1)
            _driver.set_motor_direction(-1)
            if _driver.get_floor_sensor_signal() == 1:
                _driver.set_button_lamp(2, 1, 0)
                _driver.set_motor_direction(0)
                _driver.set_door_open_lamp(1)
        pass



if __name__ == "__main__":
    main()
