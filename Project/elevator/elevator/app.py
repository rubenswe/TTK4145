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
from elevator import user_interface

logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                           " (%(module)s.%(funcName)s)",
                    level=logging.DEBUG)


def main():

    # Arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("elevator", type=int, help="Elevator number (Elevator 0 is the first elevator)")
    parser.add_argument("--mode", type=str, default="primary",
                        help="Process pairs mode (primary/backup). Default: primary")

    args = parser.parse_args()

    # Initialize modules
    node_name = "elevator_{}".format(args.elevator)

    config = core.Configuration("../config/local-test.conf", node_name)
    net = network.Network(config)
    _user_interface = user_interface.UserInterface(config)

    module_list = {
        "network": net,
        "user_interface": _user_interface,
    }

    # Starts
    pair = process_pairs.ProcessPair(config, args)
    pair.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
