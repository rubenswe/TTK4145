import logging
import transaction
import network
import core
import floor_panel
import module_base


class RequestManager(module_base.ModuleBase):
    """
    Receives user request from the user interface and sends to the appropriate
    elevator.
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__network = None
        self.__user_interface = None
        self.__elevator_monitor = None

        # Configurations
        self.__floor = None
        self.__elevator_number = None
        self.__elevator_address = None

        # Up/down request is waiting to be served
        self.__has_request = {
            core.Direction.Up: False,
            core.Direction.Down: False,
        }

        # Elevator which is serving the request
        self.__serving_elevator = {
            core.Direction.Up: -1,
            core.Direction.Down: -1,
        }

    def init(self, config, transaction_manager, _network,
             user_interface, elevator_monitor):
        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(user_interface,
                          floor_panel.user_interface.UserInterface)
        assert isinstance(elevator_monitor,
                          floor_panel.elevator_monitor.ElevatorMonitor)

        logging.debug("Start initializing request manager")
        module_base.ModuleBase.init(self, transaction_manager)

        # Related modules
        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__user_interface = user_interface
        self.__elevator_monitor = elevator_monitor

        # Configurations
        self.__floor = config.get_int("floor", "floor")
        self.__elevator_number = config.get_int("core", "elevator_number")
        self.__elevator_address = [
            (config.get_value("network", "elevator_%d.ip_address" % (index)),
             config.get_int("network", "elevator_%d.port" % (index)))
            for index in range(self.__elevator_number)
        ]

        # Registers incoming packet handlers
        _network.add_packet_handler("floor_request_served",
                                    self.__on_request_served_received)
        _network.add_packet_handler("floor_get_all_requests",
                                    self.__on_get_all_requests_received)

        logging.debug("Finish initializing request manager")

    def start(self, tid):
        """
        Starts working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start activating request manager module")

        logging.debug("Finish activating request manager module")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of request manager")

        data = {
            "has_request": self.__has_request,
            "serving_elevator": self.__serving_elevator,
        }

        logging.debug("Finish exporting current state of request manager")

        return data

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of request manager")

        self.__has_request = state["has_request"]
        self.__serving_elevator = state["serving_elevator"]

        logging.debug("Finish importing current state of request manager")

    def add_request(self, tid, direction):
        """
        Adds a new request from users. After determining the appropriate
        elevator, the request will be sent to that elevator.
        """

        assert isinstance(direction, core.Direction)

        self._join_transaction(tid)
        logging.debug("Start adding new request (tid = %s, direction = %s)",
                      tid, direction)

        if not self.__has_request[direction]:
            # Adds new request
            self.__has_request[direction] = True
            self.__serving_elevator[direction] = -1

            # Finds the appropriate elevator
            elev_no = self.__elevator_monitor.get_best_elevator(tid, direction)

            if elev_no >= 0:
                # Sends the request
                self.__send_request_to_elevator(tid, direction, elev_no)
                self.__serving_elevator[direction] = elev_no
            else:
                # All elevators are disconnected or the floor panel has lost
                # of network => Removes the request to allow user realizing it
                self.__has_request[direction] = False
                self.__user_interface.turn_button_light_off(tid, direction)
                logging.error("Cannot find any available elevator. Remove "
                              "the request (direction = %s)", direction)

        logging.debug("Finish adding new request (tid = %s, direction = %s)",
                      tid, direction)

        return True

    def __send_request_to_elevator(self, tid, direction, elevator):
        """
        Delegates the specified request to the specified elevator.
        """

        self._join_transaction(tid)
        logging.debug("Start sending the request to elevator "
                      "(direction = %s, elevator = %d)",
                      direction, elevator)
        address = self.__elevator_address[elevator]

        # Sends request to the appropriate elevator
        data = {
            "floor": self.__floor,
            "direction": direction,
        }

        logging.debug(
            "Send the request to elevator %d (addr = %s, data = %s)",
            elevator, address, data)

        resp = self.__network.send_packet(address, "elev_request_add", data)

        if resp is not True:
            logging.error(
                "Cannot send the request to elevator %d", elevator)

            return False
        else:
            logging.info("Request has been sent to elevator "
                         "(direction = %d, elevator = %d)",
                         direction, elevator)

    def on_elevator_state_changed(self, tid, elevator, state):
        """
        Occurred when the elevator state has been changed. If the elevator is
        disconnected, the requests sent to that elevator will be delegated
        to another one.
        """

        self._join_transaction(tid)
        logging.debug(
            "Start handling elevator state changed event (elevator = %d)",
            elevator)

        if not state.is_connected or state.motor_stuck:
            if not state.is_connected:
                logging.debug("The elevator %d has been disconnected!",
                              elevator)
            else:
                logging.debug("The elevator %d has been stucked!", elevator)

            # Finds all the requests delegated to this elevator and sends them
            # to another one
            for direction in self.__has_request.keys():
                if self.__has_request[direction] \
                        and self.__serving_elevator[direction] == elevator:

                    new_elevator = self.__elevator_monitor.get_best_elevator(
                        tid, direction)

                    if new_elevator >= 0:
                        logging.info("Change serving elevator of direction %s "
                                     "from %d to %d",
                                     direction, elevator, new_elevator)
                        self.__send_request_to_elevator(
                            tid, direction, new_elevator)
                        self.__serving_elevator[direction] = new_elevator
                    else:
                        # All elevators are disconnected or the floor panel has
                        # lost of network => Removes the request to allow user
                        # realizing it
                        self.__has_request[direction] = False
                        self.__user_interface.turn_button_light_off(
                            tid, direction)
                        logging.error(
                            "Cannot find any available elevator. Remove "
                            "the request (direction = %s)", direction)
        else:
            # If it have not received the request, sends again
            for direction in self.__has_request.keys():
                if self.__has_request[direction] \
                        and self.__serving_elevator[direction] == elevator \
                        and direction not in state.serving_requests:

                    logging.error("Elevator %d have not received the request "
                                  "delegated with direction %s",
                                  elevator, direction)
                    self.__send_request_to_elevator(tid, direction, elevator)

        logging.debug(
            "Finish handling elevator state changed event (elevator = %d)",
            elevator)

    def __on_request_served_received(self, tid, address, data):
        """
        Called when receiving a "request_served" packet which has sent by
        an elevator. This request then is deleted and the corresponding
        button light will be turned off.
        """

        self._join_transaction(tid)
        logging.debug("Start handling request served packet from elevator")

        # Extracts the served elevator and direction
        elevator = data["elevator"]
        direction = data["direction"]

        # Removes the request from pending request list
        self.__has_request[direction] = False

        # Turns off the button light
        self.__user_interface.turn_button_light_off(tid, direction)

        logging.info("Request has been served (direction = %d, elevator = %d)",
                     direction, elevator)

        logging.debug("Finish handling request served packet from elevator")

        return True

    def __on_get_all_requests_received(self, tid, address, data):
        """
        Called when receiving a "get_all_requests" packet which has sent by
        a read-only floor panel.
        """

        self._join_transaction(tid)
        logging.debug("Start handling \"get_all_requests\" packet")

        requests = (self.__has_request[core.Direction.Up],
                    self.__has_request[core.Direction.Down])

        logging.debug("Finish handling \"get_all_requests\" packet "
                      "(requests = %s)", requests)
        return requests
