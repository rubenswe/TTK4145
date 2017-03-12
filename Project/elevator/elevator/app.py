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
import elevator.user_interface

logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


def main():
    """
    Starts running
    """

    # Arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "elevator", type=int, help="Elevator number (from 0)")
    parser.add_argument(
        "--mode", type=str, default="primary",
        help="Process pairs mode (primary/backup). Default: primary")

    args = parser.parse_args()

    # Initializes modules
    node_name = "elevator_%d" % args.elevator

    config = core.Configuration("../config/local-test.conf", node_name)
    transaction_manager = transaction.TransactionManager()

    _network = network.Network()
    _driver = driver.Driver()
    user_interface = elevator.user_interface.UserInterface()

    _network.init(config, transaction_manager)
    _driver.init(config, transaction_manager)
    user_interface.init(config, transaction_manager, _driver)

    module_list = {
        "network": _network,
        "driver": _driver,
        "user_interface": user_interface,
    }

    # Starts
    pair = process_pairs.ProcessPair()
    pair.init(config, transaction_manager, args)
    pair.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
