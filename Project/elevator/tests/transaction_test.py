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


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


class Counter(transaction.ResourceManager):

    def __init__(self, transaction_manager):
        transaction.ResourceManager.__init__(self, transaction_manager)
        self.__count = 0

        self.__prev_state = None

    def increase(self, tid):
        self.join_transaction(tid)
        self.__prev_state = self.__count

        self.__count += 1
        logging.info("Counter is increased to %d", self.__count)

    def prepare_to_commit(self, tid):
        return True

    def commit(self, tid):
        self.leave_transaction(tid)

    def abort(self, tid):
        self.__count = self.__prev_state
        logging.info("Counter is rolled back to %d", self.__count)
        self.leave_transaction(tid)


class RandomError(transaction.ResourceManager):

    def __init__(self, transaction_manager):
        transaction.ResourceManager.__init__(self, transaction_manager)

    def do_work(self, tid):
        self.join_transaction(tid)

    def prepare_to_commit(self, tid):
        r = random.randrange(100)
        ok = r < 75
        if not ok:
            logging.error("Error occurred!")

        return ok

    def commit(self, tid):
        self.leave_transaction(tid)

    def abort(self, tid):
        self.leave_transaction(tid)


def main():
    """
    Starts
    """

    transaction_manager = transaction.TransactionManager()
    counter = Counter(transaction_manager)
    random_error = RandomError(transaction_manager)

    while True:
        tid = transaction_manager.start()
        counter.increase(tid)
        random_error.do_work(tid)
        ok = transaction_manager.finish(tid)

        time.sleep(1)

if __name__ == "__main__":
    main()
