"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import random
import transaction
import time
import module_base


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class Counter(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__count = 0

    def init(self, transaction_manager):
        module_base.ModuleBase.init(self, transaction_manager)

    def start(self):
        pass

    def export_state(self, tid):
        self._join_transaction(tid)
        return {"counter": self.__count}

    def import_state(self, tid, state):
        self._join_transaction(tid)
        self.__count = state["counter"]

    def increase(self, tid):
        self._join_transaction(tid)

        self.__count += 1
        logging.info("Counter is increased to %d", self.__count)


class RandomError(module_base.ModuleBase):

    def __init__(self):
        module_base.ModuleBase.__init__(self)

    def init(self, transaction_manager):
        module_base.ModuleBase.init(self, transaction_manager)

    def export_state(self, tid):
        self._join_transaction(tid)
        return None

    def import_state(self, tid, state):
        self._join_transaction(tid)

    def do_work(self, tid):
        self._join_transaction(tid)

        r = random.randrange(100)
        ok = r < 75
        if not ok:
            logging.error("Error occurred!")
            self._set_can_commit(tid, False)


def main():
    """
    Starts
    """

    transaction_manager = transaction.TransactionManager()

    counter = Counter()
    random_error = RandomError()

    counter.init(transaction_manager)
    random_error.init(transaction_manager)

    while True:
        tid = transaction_manager.start()
        counter.increase(tid)
        random_error.do_work(tid)
        ok = transaction_manager.finish(tid)

        time.sleep(1)

if __name__ == "__main__":
    main()
