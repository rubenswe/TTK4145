import logging
import time
import threading
import module_base
import transaction
import driver
import core


class MotorController(module_base.ModuleBase):
    """
    Motor controller which receives the destination floor from the elevator
    controller and controls the motor to reach that floor. This module also
    monitors the state of motor to recognize that the motor is working or not.
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__driver = None

        # Configurations
        self.__period = None
        self.__stuck_timeout = None

        # States
        self.__target_floor = 0
        self.__prev_floor = -1
        self.__direction = core.Direction.Stop
        self.__stuck_counter = 0
        self.__is_stuck = False

    def init(self, config, transaction_manager, _driver):
        """
        Initializes the motor controller.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)

        logging.debug("Start initializing motor controller")
        module_base.ModuleBase.init(self, transaction_manager)

        # Related modules
        self.__transaction_manager = transaction_manager
        self.__driver = _driver

        # Configurations
        self.__period = config.get_float("elevator", "motor_controller_period")
        self.__stuck_timeout = config.get_float(
            "elevator", "motor_stuck_timeout")

        logging.debug("Finish initializing motor controller")

    def start(self, tid):
        """
        Starts working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start activating the motor controller")

        threading.Thread(target=self.__control_motor_thread,
                         daemon=True).start()

        logging.debug("Finish activating the motor controller")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of motor controller")

        state = {
            "target_floor": self.__target_floor,
            "prev_floor": self.__prev_floor,
            "direction": self.__direction,
            "stuck_counter": self.__stuck_counter,
            "is_stuck": self.__is_stuck,
        }

        logging.debug("Finish exporting current state of motor controller")

        return state

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of motor controller")

        self.__target_floor = state["target_floor"]
        self.__prev_floor = state["prev_floor"]
        self.__direction = state["direction"]
        self.__stuck_counter = state["stuck_counter"]
        self.__is_stuck = state["is_stuck"]

        logging.debug("Finish importing current state of motor controller")

    def get_current_position_direction(self, tid):
        """
        Returns the current elevator position and motor direction.
        """

        self._join_transaction(tid)
        logging.debug("Start getting current position and direction")

        logging.debug("Finish getting current position and direction "
                      "(prev_floor = %d, direction = %s)",
                      self.__prev_floor, self.__direction)
        return self.__prev_floor, self.__direction

    def set_target_floor(self, tid, target_floor):
        """
        Sets the destination floor. The target floor can be changed while the
        elevator is moving. If the elevator is stopping, the motor will be
        activated automatically if the target floor is not the same with the
        current floor.
        """

        self._join_transaction(tid)
        logging.debug("Start/Finish setting target floor to %d", target_floor)
        self.__target_floor = target_floor

    def is_stuck(self, tid):
        """
        Gets the value indicates whether the motor is stuck or not.
        After a period of time if the motor cannot move, it is considered as
        stuck (not work).
        """

        self._join_transaction(tid)
        logging.debug("Start getting whether the motor is stuck")

        logging.debug("Finish getting whether the motor is stuck "
                      "(is_stuck = %s)", self.__is_stuck)
        return self.__is_stuck

    def __control_motor_thread(self):
        """
        Motor controlling thread. This thread also monitors the position
        of the elevator and can detect motor stuck or lost of power problem.
        """

        logging.debug("Start motor controlling thread")

        prev_position = -1  # Previous sensor value

        # Moves the elevator down until it reaches any floor to be able to
        # detect the current position of the elevator at initialization.
        tid = self.__transaction_manager.start()
        self._join_transaction(tid)

        if self.__prev_floor == -1:
            logging.debug("Move elevator down to any floor")
            self.__driver.set_motor_direction(driver.MotorDirection.Down)
            self.__direction = core.Direction.Down

            while True:
                self.__prev_floor = self.__driver.get_floor_sensor_signal()
                if self.__prev_floor != -1:
                    break

        self.__transaction_manager.finish(tid)

        while True:
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            # Moves up/down depends on the previous reached floor
            # and the destination floor
            if self.__prev_floor < self.__target_floor:
                if self.__direction != core.Direction.Up:
                    self.__driver.set_motor_direction(driver.MotorDirection.Up)
                    self.__direction = core.Direction.Up
            elif self.__prev_floor > self.__target_floor:
                if self.__direction != core.Direction.Down:
                    self.__driver.set_motor_direction(
                        driver.MotorDirection.Down)
                    self.__direction = core.Direction.Down

            curr_position = self.__driver.get_floor_sensor_signal()
            if curr_position == self.__target_floor:
                # Stops at the current floor
                if self.__direction != core.Direction.Stop:
                    self.__driver.set_motor_direction(
                        driver.MotorDirection.Stop)
                    self.__direction = core.Direction.Stop

            # Determines whether the motor is still running or not
            if self.__direction == core.Direction.Stop:
                self.__stuck_counter = 0
                self.__is_stuck = False
            else:
                if curr_position == prev_position:
                    if self.__period * self.__stuck_counter > \
                            self.__stuck_timeout:
                        # Timeout => The motor cannot move
                        logging.error("The motor cannot move!")
                        self.__is_stuck = True

                    self.__stuck_counter += 1
                else:
                    self.__stuck_counter = 0
                    self.__is_stuck = False
            prev_position = curr_position

            # Stores the previous reached floor
            if curr_position != -1:
                self.__prev_floor = curr_position

            _ = self.__transaction_manager.finish(tid)

            time.sleep(self.__period)
