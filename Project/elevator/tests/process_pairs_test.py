"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import time
import threading
import logging
import argparse
import core
import network
import process_pairs
import transaction
import module_base


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class Counter(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__transaction_manager = None

        self.__running = True
        self.__counter = 0

    def init(self, transaction_manager):
        module_base.ModuleBase.init(self, transaction_manager)
        self.__transaction_manager = transaction_manager

    def start(self):
        print("Start counting from %d" % (self.__counter))

        thread = threading.Thread(target=self.__count_thread, daemon=True)
        self.__running = True
        thread.start()

    def export_state(self, tid):
        self._join_transaction(tid)
        return {"counter": self.__counter}

    def import_state(self, tid, state):
        self._join_transaction(tid)
        self.__counter = state["counter"]

    def __count_thread(self):
        while self.__running:
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            self.__counter += 1
            print("Counter = %d" % (self.__counter))

            self.__transaction_manager.finish(tid)

            time.sleep(1)


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
    counter = Counter()

    net.init(config, transaction_manager)
    counter.init(transaction_manager)

    module_list = {
        "network": net,
        "counter": counter,
    }

    pp = process_pairs.ProcessPair()
    pp.init(config, transaction_manager, args)

    pp.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
