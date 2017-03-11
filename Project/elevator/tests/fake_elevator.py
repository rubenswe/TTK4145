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
import threading

logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class FakeElevator(object):

    def __init__(self, config, _network):
        self.__network = _network

        self.__floor_number = config.get_int("core", "floor_number")
        self.__requests = [[False, False, False]] * self.__floor_number

        self.__position = 0
        self.__direction = core.Direction.Up

        self.__floor_address = [
            (config.get_value("network", "floor_%d.ip_address" % (index)),
             config.get_int("network", "floor_%d.port" % (index)))
            for index in range(self.__floor_number)
        ]

        threading.Thread(target=self.__elevator_moving_thread,
                         daemon=True).start()

    def __elevator_moving_thread(self):
        while True:
            req = self.__requests[self.__position]
            has_internal = req[2]
            has_up = (req[0] and self.__direction == core.Direction.Up)
            has_down = (req[1] and self.__direction == core.Direction.Down)

            if has_internal or has_up or has_down:
                if has_internal:
                    req[2] = False
                if has_up:
                    ok = self.__network.send_packet(
                        self.__floor_address[self.__position],
                        "floor_request_served",
                        {"elevator": 0, "direction": core.Direction.Up})
                    if ok:
                        req[0] = False
                if has_down:
                    ok = self.__network.send_packet(
                        self.__floor_address[self.__position],
                        "floor_request_served",
                        {"elevator": 0, "direction": core.Direction.Down})
                    if ok:
                        req[1] = False

                time.sleep(1)

            if self.__direction == core.Direction.Up:
                self.__position += 1
            elif self.__direction == core.Direction.Down:
                self.__position -= 1
            if self.__position == 0:
                self.__direction = core.Direction.Up
            elif self.__position == self.__floor_number - 1:
                self.__direction = core.Direction.Down

            time.sleep(1)

    def on_elev_request_add_received(self, tid, addr, data):
        floor = data["floor"]
        direction = data["direction"]

        if direction == core.Direction.Up:
            self.__requests[floor][0] = True
        elif direction == core.Direction.Down:
            self.__requests[floor][1] = True

        return True

    def on_elev_state_get_received(self, tid, addr, data):
        floor = data["floor"]
        serving_requests = list()
        if self.__requests[floor][0]:
            serving_requests.append(core.Direction.Up)
        elif self.__requests[floor][1]:
            serving_requests.append(core.Direction.Down)

        state = {
            "position": self.__position,
            "direction": self.__direction,
            "serving_requests": serving_requests,
        }

        return state


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
    node_name = "elevator_0"  # input("Node name: ")

    config = core.Configuration("../config/local-test.conf", node_name)
    transaction_manager = transaction.TransactionManager()
    net = network.Network()
    net.init(config, transaction_manager)

    fake = FakeElevator(config, net)

    net.add_packet_handler(
        "elev_request_add", fake.on_elev_request_add_received)
    net.add_packet_handler(
        "elev_state_get", fake.on_elev_state_get_received)

    net.start()

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
