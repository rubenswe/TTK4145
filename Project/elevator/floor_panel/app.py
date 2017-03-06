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
import floor_panel.user_interface

logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.DEBUG)


def main():
    """
    Starts running
    """

    # Arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "floor", type=int, help="Floor number (Floor 0 is the first floor)")
    parser.add_argument(
        "--mode", type=str, default="primary",
        help="Process pairs mode (primary/backup). Default: primary")

    args = parser.parse_args()

    # Initializes modules
    node_name = "floor_%d" % args.floor

    config = core.Configuration("../config/local-test.conf", node_name)
    net = network.Network(config)
    transaction_manager = transaction.TransactionManager()
    _driver = driver.Driver(config)

    user_interface = floor_panel.user_interface.UserInterface()
    user_interface.init(config, transaction_manager, _driver)

    module_list = {
        "network": net,
        "driver": _driver,
        "user_interface": user_interface,
    }

    # Starts
    pair = process_pairs.ProcessPair(config, args)
    pair.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
