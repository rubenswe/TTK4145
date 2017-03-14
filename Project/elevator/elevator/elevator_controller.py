import logging
import threading
import time
import module_base
import core
import transaction
import enum
import elevator
import driver
import network


class ElevatorState(enum.IntEnum):
    """
    Elevator states:
      - Stop: stopping, no request
      - Move: moving to a floor
      - Stay: stopping for awhile, still has other request
    """

    Stop = 0,
    Move = 1,
    Stay = 2,


class ElevatorController(module_base.ModuleBase):
    """
    Controls and monitors the elevator. This module gets the current list
    of requests from the request manager, determines the state and next
    destination of the elevator and call the motor controller to reach
    that floor.
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__request_manager = None
        self.__motor_controller = None
        self.__user_interface = None

        # Configurations
        self.__floor_number = None
        self.__period = None
        self.__stay_time = None

        # States
        self.__state = ElevatorState.Stop
        self.__direction = core.Direction.Stop
        self.__prev_time = None  # For stay timer

    def init(self, config, transaction_manager, _network,
             request_manager, motor_controller, user_interface):
        """
        Initializes the elevator controller.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(request_manager,
                          elevator.request_manager.RequestManager)
        assert isinstance(motor_controller,
                          elevator.motor_controller.MotorController)
        assert isinstance(user_interface,
                          elevator.user_interface.UserInterface)

        logging.debug("Start initializing elevator controller")
        module_base.ModuleBase.init(self, transaction_manager)

        # Related modules
        self.__transaction_manager = transaction_manager
        self.__request_manager = request_manager
        self.__motor_controller = motor_controller
        self.__user_interface = user_interface

        # Configurations
        self.__floor_number = config.get_int("core", "floor_number")
        self.__period = config.get_float(
            "elevator", "elevator_control_period")
        self.__stay_time = config.get_float("elevator", "stay_time")

        # Registers incoming packet handler
        _network.add_packet_handler("elev_state_get",
                                    self.__on_elev_state_get_received)

        logging.debug("Finish initializing elevator controller")

    def start(self, tid):
        """
        Starts working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start activating elevator controller")

        # Starts elevator controlling thread
        threading.Thread(target=self.__control_thread,
                         daemon=True).start()

        logging.debug("Finish activating elevator controller")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of elevator controller")

        state = {
            "state": self.__state,
            "direction": self.__direction,
            "prev_time": self.__prev_time,
        }

        logging.debug("Finish exporting current state of elevator controller")
        return state

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of elevator controller")

        self.__state = state["state"]
        self.__direction = state["direction"]
        self.__prev_time = state["prev_time"]

        logging.debug("Finish importing current state of elevator controller")

    def __on_elev_state_get_received(self, tid, address, data):
        """
        Called when the elevator controller receives a packet from floor
        panels which asks the current state (position, direction, etc.)
        of this elevator.
        """

        self._join_transaction(tid)
        logging.debug("Start handling the \"elev_state_get\" packet "
                      "from floor %d", data["floor"])

        floor = data["floor"]

        # Gets list of requests belongs to that floor
        logging.debug("Get current list of request from request manager")

        requests = self.__request_manager.get_current_request_list(tid)
        serving_requests = list()
        if requests[floor].call_up:
            serving_requests.append(core.Direction.Up)
        if requests[floor].call_down:
            serving_requests.append(core.Direction.Down)

        # Gets current motor state
        logging.debug("Get current state of motor controller")

        motor_position, _ = \
            self.__motor_controller.get_current_position_direction(tid)
        motor_stuck = self.__motor_controller.is_stuck(tid)

        # Sends back the state
        return {
            "position": motor_position,
            "direction": self.__direction,
            "serving_requests": serving_requests,
            "motor_stuck": motor_stuck,
        }

        logging.debug("Finish handling the \"elev_state_get\" packet "
                      "from floor %d", floor)

    def __control_thread(self):
        """
        Elevator main controlling finite state manchine.
        """

        logging.debug("Start controlling the elevator")

        while True:
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            # Gets the current list of requests from the request manager
            requests = self.__request_manager.get_current_request_list(tid)

            # Gets the current motor state
            motor_position, motor_direction = \
                self.__motor_controller.get_current_position_direction(tid)

            # Finds the next destination floor
            target_floor = self.__find_next_destination(
                tid, motor_position, requests)

            # Determines the next state of the elevator
            if self.__state == ElevatorState.Move:
                self.__user_interface.set_floor_indicator(tid, motor_position)

                if motor_direction == driver.MotorDirection.Stop:
                    logging.debug("The elevator has reached the desired floor "
                                  "(floor = %d, direction = %s)",
                                  motor_position, self.__direction)

                    # Changes to stay state
                    logging.info("Elevator stays at floor %d (direction = %s)",
                                 motor_position, self.__direction)

                    self.__prev_time = time.time()
                    self.__state = ElevatorState.Stay

                    # Changes the direction if neccessary
                    if self.__direction == core.Direction.Up:
                        if target_floor is None \
                                and not requests[motor_position].call_up \
                                and requests[motor_position].call_down:
                            self.__direction = core.Direction.Down
                    if self.__direction == core.Direction.Down:
                        if target_floor is None \
                                and not requests[motor_position].call_down \
                                and requests[motor_position].call_up:
                            self.__direction = core.Direction.Up

                    # Sends request has served to request manager
                    self.__request_manager.set_request_served(
                        tid, motor_position, self.__direction)
                else:  # The elevator is on the way
                    if target_floor is not None:  # Just for sure
                        self.__motor_controller.set_target_floor(
                            tid, target_floor)

            elif self.__state == ElevatorState.Stay:
                timeout = (time.time() - self.__prev_time >= self.__stay_time)
                self.__user_interface.set_door_open_light(tid, True)

                if target_floor is not None:
                    if target_floor == motor_position:
                        # If user pushes the button of the same floor,
                        # resets the timer
                        self.__prev_time = time.time()
                        self.__request_manager.set_request_served(
                            tid, motor_position, self.__direction)
                    elif timeout:  # Timeout => Moves to that floor
                        logging.info("Elevator starts moving from %d to %d",
                                     motor_position, target_floor)

                        if target_floor > motor_position:
                            self.__direction = core.Direction.Up
                        else:
                            self.__direction = core.Direction.Down

                        self.__state = ElevatorState.Move

                        self.__user_interface.set_door_open_light(tid, False)
                        self.__motor_controller.set_target_floor(
                            tid, target_floor)

                    pass
                elif timeout and target_floor is None:
                    # Changes to stop state
                    logging.info("Elevator stops at floor %d (direction = %s)",
                                 motor_position, self.__direction)

                    self.__state = ElevatorState.Stop
                    self.__direction = core.Direction.Stop

                    self.__user_interface.set_door_open_light(tid, False)
            elif self.__state == ElevatorState.Stop:
                if target_floor is not None:
                    if target_floor == motor_position:  # Just opens the door
                        logging.info(
                            "Elevator stays at floor %d (direction = %s)",
                            target_floor, self.__direction)

                        # Switches to stay state
                        self.__prev_time = time.time()
                        self.__state = ElevatorState.Stay

                        # Sends request has served to request manager
                        if requests[motor_position].call_up:
                            direction = core.Direction.Up
                        elif requests[motor_position].call_down:
                            direction = core.Direction.Down
                        else:
                            direction = core.Direction.Stop

                        self.__request_manager.set_request_served(
                            tid, motor_position, direction)
                    else:
                        logging.info("Elevator starts moving from %d to %d",
                                     motor_position, target_floor)

                        # Switches to move state and moves to that floor
                        if target_floor > motor_position:
                            self.__direction = core.Direction.Up
                        else:
                            self.__direction = core.Direction.Down

                        self.__state = ElevatorState.Move
                        self.__motor_controller.set_target_floor(
                            tid, target_floor)

            self.__transaction_manager.finish(tid)

            time.sleep(self.__period)

        # Never reach here

    def __find_next_destination(self, tid, curr_floor, requests):
        """
        Returns the nearest next destination. This function only returns
        the destination the elevator can reach without changing direction.
        If it needs to change direction, it must be changed by the main
        FSM, not here to make sure the elevator always prefer maintaining
        its direction.
        """

        self._join_transaction(tid)

        next_destination = None

        # Considers the current floor if it is staying or stopping
        # When users push the current floor button, the elevator should
        # serve that request by keep the door open.
        if self.__state != ElevatorState.Move:
            if self.__direction == core.Direction.Up \
                    and requests[curr_floor].call_up:
                return curr_floor
            if self.__direction == core.Direction.Down \
                    and requests[curr_floor].call_down:
                return curr_floor
            if requests[curr_floor].cabin:
                return curr_floor
            if self.__state == ElevatorState.Stop \
                    and (requests[curr_floor].call_up or
                         requests[curr_floor].call_down):
                return curr_floor

        if self.__direction == core.Direction.Up \
                or self.__direction == core.Direction.Stop:

            # Looks up for the nearest "up" request
            for floor in range(curr_floor + 1, self.__floor_number):
                if requests[floor].call_up \
                        or requests[floor].cabin:
                    next_destination = floor
                    break

            if next_destination is None:  # No "up" request exists
                # Looks up for the farthest "down" request
                for floor in reversed(range(
                        curr_floor + 1, self.__floor_number)):
                    if requests[floor].call_down:
                        next_destination = floor
                        break

        if self.__direction == core.Direction.Down \
                or self.__direction == core.Direction.Stop:
            # Looks down for the nearest "down" request
            for floor in reversed(range(0, curr_floor)):
                if requests[floor].call_down \
                        or requests[floor].cabin:
                    next_destination = floor
                    break

            if next_destination is None:  # No "down" request exists
                # Looks down for the farthest "up" request
                for floor in range(0, curr_floor):
                    if requests[floor].call_up:
                        next_destination = floor
                        break

        return next_destination
