import logging
import random
import transaction
import time
import module_base
import threading


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


def thread1(index, transaction_manager, counter, random_error):
    while True:
        print("-------------- %d -----------------" % (index))
        tid = transaction_manager.start()
        counter.increase(tid)
        random_error.do_work(tid)
        transaction_manager.finish(tid)

        time.sleep(1)


def main():
    """
    Starts
    """

    transaction_manager = transaction.TransactionManager()

    counter = Counter()
    random_error = RandomError()

    counter.init(transaction_manager)
    random_error.init(transaction_manager)

    threading.Thread(target=thread1,
                     args=(1, transaction_manager, counter, random_error),
                     daemon=True).start()
    threading.Thread(target=thread1,
                     args=(2, transaction_manager, counter, random_error),
                     daemon=True).start()

    while True:
        time.sleep(100)

if __name__ == "__main__":
    main()
