"""
Created on Feb 9, 2017

@author: Viet-Hoa Do
"""

import time
import threading
import logging
import argparse
import core
import network
import process_pairs
import driver
import transaction


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.DEBUG)


def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", type=str, default="primary",
        help="Process pairs mode (primary/backup). Default: primary")
    args = parser.parse_args()

    # Initializes
    config = core.Configuration("../config/local-test.conf", "floor_0")
    transaction_manager = transaction.TransactionManager()

    net = network.Network()
    drv = driver.Driver()

    net.init(config, transaction_manager)
    drv.init(config, transaction_manager)

    module_list = {
        "network": net,
        "driver": drv,
    }

    pp = process_pairs.ProcessPair()
    pp.init(config, transaction_manager, args)
    pp.start(module_list)

    drv.set_motor_direction(1)

    while True:
        logging.debug("up_0: %d, up_1: %d, up_2: %d, down_1: %d, down_2: %d, down_3: %d, 0: %d, 1: %d, 2: %d, 3: %d, floor: %d",
                      drv.get_button_signal(0, 0),
                      drv.get_button_signal(0, 1),
                      drv.get_button_signal(0, 2),
                      drv.get_button_signal(1, 1),
                      drv.get_button_signal(1, 2),
                      drv.get_button_signal(1, 3),
                      drv.get_button_signal(2, 0),
                      drv.get_button_signal(2, 1),
                      drv.get_button_signal(2, 2),
                      drv.get_button_signal(2, 3),
                      drv.get_floor_sensor_signal()
                      )

    while True:
        if drv.get_floor_sensor_signal() == 3:
            drv.set_motor_direction(-1)
        elif drv.get_floor_sensor_signal() == 0:
            drv.set_motor_direction(1)

        if drv.get_stop_signal() == 1:
            drv.set_motor_direction(0)
            break

if __name__ == "__main__":
    main()
