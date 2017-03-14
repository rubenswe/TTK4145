import logging
import argparse
import time
import threading
import core
import network
import process_pairs
import transaction
import driver
import module_base

logging.basicConfig(
    format="%(process)d | %(levelname)8s | %(asctime)s : %(message)s"
    " (%(module)s.%(funcName)s)",
    level=logging.INFO)


class FloorReadonly(module_base.ModuleBase):
    """
    This is a special node which only shows all the floor panels lights
    without any button interaction.
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__network = None
        self.__driver = None

        # Configurations
        self.__period = None
        self.__floor_number = None
        self.__floor_address = None

    def init(self, config, transaction_manager, _network, _driver):
        """
        Initializes the read-only floor panel module.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(_driver, driver.Driver)

        logging.debug("Start initializing read-only floor panel")
        module_base.ModuleBase.init(self, transaction_manager)

        # Related modules
        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__driver = _driver

        # Configurations
        self.__period = config.get_float("floor", "readonly_period")
        self.__floor_number = config.get_int("core", "floor_number")
        self.__floor_address = [
            (config.get_value("network", "floor_%d.ip_address" % (index)),
             config.get_int("network", "floor_%d.port" % (index)))
            for index in range(self.__floor_number)
        ]

        logging.debug("Finish initializing read-only floor panel")

    def start(self, tid):
        """
        Starts working from the current state
        """

        self._join_transaction(tid)
        logging.debug("Start activating read-only floor panel "
                      "from current state")

        threading.Thread(target=self.__show_floor_button_light_thread,
                         daemon=True).start()

        logging.debug("Finish activating read-only floor panel "
                      "from current state")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        return dict()

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)

    def __show_floor_button_light_thread(self):
        """
        Periodically gets the current requests from all the floor panels
        and shows them on the button lights.
        """

        while True:
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            for floor in range(self.__floor_number):

                logging.debug("Get floor %d request list", floor)
                resp = self.__network.send_packet(
                    self.__floor_address[floor],
                    "floor_get_all_requests",
                    True)

                if resp is not False:
                    logging.debug("Update button lights of floor %d", floor)

                    call_up, call_down = resp
                    if call_up:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallUp, floor, 1)
                    else:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallUp, floor, 0)

                    if call_down:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallDown, floor, 1)
                    else:
                        self.__driver.set_button_lamp(
                            driver.FloorButton.CallDown, floor, 0)

            self.__transaction_manager.finish(tid)

            time.sleep(self.__period)


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
    node_name = "floor_readonly"

    config = core.Configuration("../config/local-test.conf", node_name)
    transaction_manager = transaction.TransactionManager()

    _network = network.Network()
    _driver = driver.Driver()
    floor_readonly = FloorReadonly()

    _network.init(config, transaction_manager)
    _driver.init(config, transaction_manager)
    floor_readonly.init(config, transaction_manager, _network, _driver)

    module_list = {
        "network": _network,
        "driver": _driver,
        "floor_readonly": floor_readonly,
    }

    # Starts
    pair = process_pairs.ProcessPair()
    pair.init(config, transaction_manager, args)
    pair.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
