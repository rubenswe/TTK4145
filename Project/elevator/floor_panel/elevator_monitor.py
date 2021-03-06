import logging
import threading
import time
import core
import transaction
import network
import module_base
import floor_panel.request_manager


class ElevatorState(object):
    """
    State of elevator, including:
      - Position
      - Direction (going up/down, stopping)
      - Connected/disconnected
      - Serving requests from this floor
    To reduce complexity, all fields are public and directly accessible by
    the ElevatorMonitor class.
    """

    def __init__(self):
        self.position = 0
        self.direction = core.Direction.Stop
        self.is_connected = False
        self.motor_stuck = False
        self.serving_requests = set()


class ElevatorMonitor(module_base.ModuleBase):
    """
    Monitors the current state of all elevators, including:
      - Position
      - Direction (going up/down, stopping)
      - Connected/disconnected
      - Serving requests from this floor
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        logging.debug("Start initializing elevator monitor")

        # Related modules
        self.__transaction_manager = None
        self.__network = None

        # Configurations
        self.__floor_number = None
        self.__floor = None
        self.__elevator_number = None
        self.__period = None
        self.__max_attempts = None
        self.__elevator_address = None

        # States
        self.__elevator_list = None

        logging.debug("Finish initializing elevator monitor")

    def init(self, config, transaction_manager, _network, request_manager):
        """
        Initializes the elevator monitor module.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(
            request_manager, floor_panel.request_manager.RequestManager)

        logging.debug("Start initializing elevator monitor module")
        module_base.ModuleBase.init(self, transaction_manager)

        # Related modules
        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__request_manager = request_manager

        # Reads the configurations
        self.__floor_number = config.get_int("core", "floor_number")
        self.__floor = config.get_int("floor", "floor")
        self.__elevator_number = config.get_int("core", "elevator_number")
        self.__period = config.get_float("floor", "elevator_monitor_period")
        self.__max_attempts = config.get_int(
            "floor", "elevator_monitor_attempts")
        self.__elevator_address = [
            (config.get_value("network", "elevator_%d.ip_address" % (index)),
             config.get_int("network", "elevator_%d.port" % (index)))
            for index in range(self.__elevator_number)
        ]

        # Initializes state
        self.__elevator_list = [ElevatorState()
                                for i in range(self.__elevator_number)]

        logging.debug("Finish initializing elevator monitor module")

    def start(self, tid):
        """
        Starts working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start activating elevator monitor module")

        # Starts new threads to periodically retrieve the current state
        # of all the elevators
        for index in range(self.__elevator_number):
            threading.Thread(target=self.__monitor_elevator_state_thread,
                             daemon=True,
                             args=(index,)).start()

        logging.debug("Finish activating elevator monitor module")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of elevator monitor")

        state = {
            "elevator_list": self.__elevator_list,
        }

        logging.debug("Finish exporting current state of elevator monitor")

        return state

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of elevator monitor")

        self.__elevator_list = state["elevator_list"]

        logging.debug("Finish importing current state of elevator monitor")

    def get_best_elevator(self, tid, direction):
        """
        Returns the most appropriate elevator for serving the specified request
        direction.
        """

        self._join_transaction(tid)
        logging.debug("Start finding the best elevator for direction %s",
                      direction)

        # Calculates the distance of all elevators
        min_distance = self.__floor_number * 4
        best_elevator = -1

        for index in range(self.__elevator_number):
            state = self.__elevator_list[index]

            if state.is_connected and not state.motor_stuck:
                elev_position = state.position
                elev_direction = state.direction
                distance = 0

                # Calculates the worst-case distance
                if elev_direction == core.Direction.Up:
                    if direction == core.Direction.Up:
                        if elev_position < self.__floor:
                            # Just goes up directly to this floor
                            distance = self.__floor - elev_position
                        else:
                            # Goes to top, down to 0 and up to this floor
                            distance = \
                                (self.__floor_number - 1) - elev_position + \
                                (self.__floor_number - 1) + \
                                self.__floor
                    else:
                        # Goes to top floor and down to this floor
                        distance = \
                            (self.__floor_number - 1) - elev_position + \
                            (self.__floor_number - 1) - self.__floor
                elif elev_direction == core.Direction.Down:
                    if direction == core.Direction.Up:
                        # Goes down 0 and up to this floor
                        distance = elev_position + self.__floor
                    else:
                        if elev_position > self.__floor:
                            # Just goes down directly to this floor
                            distance = elev_position - self.__floor
                        else:
                            # Goes down 0, up to top and down to this floor
                            distance = elev_position + \
                                (self.__floor_number - 1) + \
                                (self.__floor_number - 1) - self.__floor
                else:
                    # Stop => Just go directly to this floor
                    if elev_position > self.__floor:
                        distance = elev_position - self.__floor
                    else:
                        distance = self.__floor - elev_position

                # If it is the shortest distance, saves it
                logging.debug("Elevator %d: distance %d", index, distance)
                if distance < min_distance:
                    min_distance = distance
                    best_elevator = index
            else:
                logging.error("Elevator %d is dead", index)

        if best_elevator == -1:
            logging.error("Cannot find any available elevator!")

        logging.debug("Finish finding the best elevator for direction %s",
                      direction)
        return best_elevator

    def __monitor_elevator_state_thread(self, index):
        """
        Monitors the specified elevator state.
        """

        logging.debug("Start elevator %d monitoring thread", index)

        attempts = 0
        address = self.__elevator_address[index]

        out_data = {"floor": self.__floor}

        while True:
            logging.debug("Ask elevator %d for its current state", index)

            # Sends request to get the current elevator state
            attempts += 1
            new_state = self.__network.send_packet(
                address, "elev_state_get", out_data)

            # Starts new transaction to update the data
            tid = self.__transaction_manager.start()
            self._join_transaction(tid)

            state = self.__elevator_list[index]

            if new_state is not False:
                logging.debug(
                    "Elevator %d current state: %s", index, new_state)

                state.is_connected = True
                attempts = 0

                state.position = new_state["position"]
                state.direction = new_state["direction"]
                state.serving_requests = new_state["serving_requests"]
                state.motor_stuck = new_state["motor_stuck"]
            else:
                logging.error(
                    "Cannot get the state of elevator %d (attempt: %d)",
                    index, attempts)

                # After some failed attempts, the elevator is considered as
                # disconnected and the request manager has to rearrange their
                # request to another one
                if attempts > self.__max_attempts:
                    state.is_connected = False

            self.__request_manager.on_elevator_state_changed(tid, index, state)
            _ = self.__transaction_manager.finish(tid)

            # Waits for a while
            time.sleep(self.__period)

        # Never end here
