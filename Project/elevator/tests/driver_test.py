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
import driver


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.DEBUG)


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
    drv = driver.Driver(config)

    module_list = {
        "network": net,
        "driver": drv,
    }

    pp = process_pairs.ProcessPair(config, args)
    pp.start(module_list)

    #drv.set_motor_direction()
    #drv.set_button_lamp(2, 2, 1)  # Button type 2 is for commands from the elevator panel
    while True:

        # if drv.get_button_signal(2, 1):
        #     drv.set_button_lamp(2, 1, 1)
        #     drv.set_motor_direction(-1)
        # if drv.get_floor_sensor_signal() == 1:
        #     drv.set_button_lamp(2, 1, 0)
        #     drv.set_motor_direction(0)
        #     drv.set_door_open_lamp(1)


        if drv.get_button_signal(2, 0):
            logging.debug("Elevator panel: Button to floor 1 is pushed")
            #drv.set_button_lamp(2, 0, 1)
        elif drv.get_button_signal(2, 1):
             logging.debug("Elevator panel: Button to floor 2 is pushed")
            #drv.set_button_lamp(2, 1, 1)
        elif drv.get_button_signal(2, 2):
            logging.debug("Elevator panel: Button to floor 3 is pushed")
            #drv.set_button_lamp(2, 2, 1)
        elif drv.get_button_signal(2, 3):
            logging.debug("Elevator panel: Button to floor 4 is pushed")
            #drv.set_button_lamp(2, 3, 1)

        #if drv.get_floor_sensor_signal() == 0:
         #   drv.set_door_open_lamp(1)
          #  drv.set_motor_direction(0)
           # break
        #elif drv.get_floor_sensor_signal() == 0:
        #     drv.set_motor_direction(1)
        #
        # if drv.get_stop_signal() == 1:
        #     drv.set_motor_direction(0)
        #     break

if __name__ == "__main__":
    main()
