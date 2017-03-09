'''
Created on Mar 9, 2017

@author: Viet-Hoa
'''

import logging
import argparse
import time
import process_pairs
import floor_panel
import core
import network
import driver
import transaction

logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class FakeNode(object):

    def __init__(self):
        pass

    def on_elev_request_add_received(self, addr, data):
        return True


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
    node_name = input("Node name: ")

    config = core.Configuration("../config/local-test.conf", node_name)
    net = network.Network(config)
    fake = FakeNode()

    net.add_packet_handler(
        "elev_request_add", fake.on_elev_request_add_received)

    net.start()

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
