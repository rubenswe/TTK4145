import logging
import argparse
import time
import core
import network
import process_pairs
import transaction
import driver
import floor_panel.user_interface
import floor_panel.request_manager
import floor_panel.elevator_monitor

logging.basicConfig(
    format="%(process)d | %(levelname)8s | %(asctime)s : %(message)s"
    " (%(module)s.%(funcName)s)",
    level=logging.INFO)


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
    transaction_manager = transaction.TransactionManager()

    _network = network.Network()
    _driver = driver.Driver()
    user_interface = floor_panel.user_interface.UserInterface()
    request_manager = floor_panel.request_manager.RequestManager()
    elevator_monitor = floor_panel.elevator_monitor.ElevatorMonitor()

    _network.init(config, transaction_manager)
    _driver.init(config, transaction_manager)
    user_interface.init(config, transaction_manager, _driver, request_manager)
    request_manager.init(config, transaction_manager, _network,
                         user_interface, elevator_monitor)
    elevator_monitor.init(config, transaction_manager, _network,
                          request_manager)

    module_list = {
        "network": _network,
        "driver": _driver,
        "user_interface": user_interface,
        "request_manager": request_manager,
        "elevator_monitor": elevator_monitor,
    }

    # Starts
    pair = process_pairs.ProcessPair()
    pair.init(config, transaction_manager, args)
    pair.start(module_list)

    while True:
        time.sleep(1000)

if __name__ == "__main__":
    main()
