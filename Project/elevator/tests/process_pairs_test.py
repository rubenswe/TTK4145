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


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class Counter(process_pairs.PrimaryBackupSwitchable):

    def __init__(self):
        self.__lock_state = threading.Lock()

        self.__counter = 0
        self.__running = True

    def start(self):
        print("Start counting from %d" % (self.__counter))

        thread = threading.Thread(target=self.__count_thread, daemon=True)
        self.__running = True
        thread.start()

    def __count_thread(self):
        while self.__running:
            self.__lock_state.acquire()
            self.__counter += 1
            print("Counter = %d" % (self.__counter))
            self.__lock_state.release()

            time.sleep(1)

    def export_state(self):
        self.__lock_state.acquire()
        state = {"counter": self.__counter}
        self.__lock_state.release()

        return state

    def import_state(self, state):
        self.__lock_state.acquire()
        self.__counter = state["counter"]
        self.__lock_state.release()


def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", type=str, default="primary",
        help="Process pairs mode (primary/backup). Default: primary")
    args = parser.parse_args()

    # Initializes
    config = core.Configuration("../config/local-test.conf", "floor_0")
    net = network.Network(config)
    counter = Counter()

    module_list = {
        "network": net,
        "counter": counter
    }

    pp = process_pairs.ProcessPair(config, args)
    pp.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
