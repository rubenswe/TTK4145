import logging
import driver
import threading
import core
from time import sleep


class MotorController(object):
    """
    Controls the elevator motor
    """

    def __init__(self, config, _driver):
        """
        Initializes the motor controller
        """

        assert isinstance(_driver, driver.Driver)

        self.__driver = _driver
        self.__target = 0
        self.__prev_pos = 0
        self.__curr_pos = 0

    def start(self):
        """
        Starts working from the current state
        """
        logging.debug("Start activating user interface module")
        threading.Thread(target=self.__elevator_monitor_thread, daemon=True).start()
        logging.debug("Finish activating user interface module")

    def export_state(self):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of user interface")
        logging.debug("Finish exporting current state of user interface")
        # return state

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of user interface")
        logging.debug("Finish importing current state of user interface")

    def get_position(self):
        """
        Returns the current position of the elevator
        """

        floor = self.__driver.get_floor_sensor_signal()
        if floor != -1:
            # logging.debug("--- The elevator is at floor *{}* ---".format(floor+1))
            return floor
        else:
            # logging.debug("The elevator is not at any floor at the moment")
            return -1

    def go_to_floor(self, floor):
        """
        Sets the direction of the elevator depending on the given floor
        """
        # Should ONLY set target floor

        if self.get_position() != floor:
            if floor == 0:
                self.__driver.set_motor_direction(-1)
                logging.debug("Going to floor *{}*".format(floor+1))

            elif floor == 1 and self.get_position() < floor:
                self.__driver.set_motor_direction(1)
                logging.debug("Going to floor *{}*".format(floor+1))
            elif floor == 1 and self.get_position() > floor:
                self.__driver.set_motor_direction(-1)
                logging.debug("Going to floor *{}*".format(floor+1))

            elif floor == 2 and self.get_position() < floor:
                self.__driver.set_motor_direction(1)
                logging.debug("Going to floor *{}*".format(floor+1))
            elif floor == 2 and self.get_position() > floor:
                self.__driver.set_motor_direction(-1)
                logging.debug("Going to floor *{}*".format(floor+1))

            elif floor == 3:
                self.__driver.set_motor_direction(1)
                logging.debug("Going to floor *{}*".format(floor + 1))

        else:
            logging.debug("The elevator is already at this floor! (Floor: *{}*)".format(floor+1))

    # get_target floor?
    # def go_to_floor(self, target):
        """
        Returns the target floor
        """
        # Should ONLY set the target floor
        # you get the target floor from driver.get_button signal(2, floor)
        # self.__driver.get_button_signal(2, target):
        # self.__target = target


    def __elevator_monitor_thread(self):
        """
        Periodically checks the position of the elevator
        """

        logging.debug("Start monitoring elevator position")

        floors = [0, 0, 0, 0]  # should come from config?

        while True:

            # Checks each elevator position(floor)
            for pos in range(len(floors)):

                    # target should be set by go_to_floor
                    self.__curr_pos = self.get_position()
                    if self.__prev_pos < self.__target:
                        self.__driver.set_motor_direction(1)
                    if self.__prev_pos > self.__target:
                        self.__driver.set_motor_direction(-1)
                    self.get_position()
                    if self.__curr_pos == self.__target:
                        self.__driver.set_motor_direction(0)
                    if self.__curr_pos != -1:
                        self.__prev_pos = self.__curr_pos
