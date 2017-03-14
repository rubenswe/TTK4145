import logging
import argparse
import core
import network
import process_pairs
import driver
import transaction
import elevator.motor_controller


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", type=str, default="primary",
        help="Process pairs mode (primary/backup). Default: primary")
    args = parser.parse_args()

    # Initializes
    config = core.Configuration("../config/local-test.conf", "elevator_0")
    transaction_manager = transaction.TransactionManager()

    net = network.Network()
    drv = driver.Driver()
    motor_controller = elevator.motor_controller.MotorController()

    net.init(config, transaction_manager)
    drv.init(config, transaction_manager)
    motor_controller.init(config, transaction_manager, drv)

    module_list = {
        "network": net,
        "driver": drv,
        "motor_controller": motor_controller
    }

    pp = process_pairs.ProcessPair()
    pp.init(config, transaction_manager, args)
    pp.start(module_list)

    while True:
        floor = input("Target floor: ")

        tid = transaction_manager.start()
        motor_controller.set_target_floor(tid, int(floor))
        transaction_manager.finish(tid)

if __name__ == "__main__":
    main()
