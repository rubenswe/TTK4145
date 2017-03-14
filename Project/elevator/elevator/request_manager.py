import logging
import module_base
import core
import transaction
import network
import elevator
import enum


class RequestTableRow(object):
    """
    Stores all the request belongs to a floor, including the call up and
    call down requests from floor panel and the request to that floor
    from the panel inside the elevator cabin.
    """

    def __init__(self):
        self.call_up = False
        self.call_down = False
        self.cabin = False


class RequestManager(module_base.ModuleBase):
    """
    Manages the list of requests from the panel inside the elevator cabin
    and the requests delegated by floor panels.
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__network = None
        self.__motor_controller = None
        self.__user_interface = None

        # Configurations
        self.__elevator = None
        self.__floor_number = None
        self.__period = None
        self.__stay_time = None
        self.__floor_address = None

        # State
        self.__request_floors = None

    def init(self, config, transaction_manager, _network,
             motor_controller, user_interface):
        """
        Initializes the request manager module.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_network, network.Network)
        assert isinstance(motor_controller,
                          elevator.motor_controller.MotorController)
        assert isinstance(user_interface,
                          elevator.user_interface.UserInterface)

        logging.debug("Start initializing request manager")
        module_base.ModuleBase.init(self, transaction_manager)

        # Related modules
        self.__transaction_manager = transaction_manager
        self.__network = _network
        self.__motor_controller = motor_controller
        self.__user_interface = user_interface

        # Configurations
        self.__elevator = config.get_int("elevator", "elevator")
        self.__floor_number = config.get_int("core", "floor_number")
        self.__period = config.get_float("elevator", "elevator_control_period")
        self.__stay_time = config.get_float("elevator", "stay_time")
        self.__floor_address = [
            (config.get_value("network", "floor_%d.ip_address" % (index)),
             config.get_int("network", "floor_%d.port" % (index)))
            for index in range(self.__floor_number)
        ]

        # State
        self.__request_floors = [
            RequestTableRow() for i in range(self.__floor_number)
        ]

        # Registers imcoming packet handler
        _network.add_packet_handler("elev_request_add",
                                    self.__on_elev_request_add_received)

        logging.debug("Finish initializing request manager")

    def start(self, tid):
        """
        Start working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start/Finish activating the request manager")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of request manager")

        state = {
            "request_floors": self.__request_floors,
        }

        logging.debug("Finish exporting current state of request manager")
        return state

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of request manager")

        self.__request_floors = state["request_floors"]

        logging.debug("Finish importing current state of request manager")

    def add_cabin_request(self, tid, floor):
        """
        Adds a request from panel inside elevator cabin. This function is
        called by the user interface module.
        """

        self._join_transaction(tid)
        logging.debug("Start adding a new cabin request (floor = %d)", floor)

        logging.info("Add cabin request to floor %d", floor)
        self.__request_floors[floor].cabin = True

        logging.debug("Finish adding a new cabin request (floor = %d)", floor)

    def __on_elev_request_add_received(self, tid, address, data):
        """
        Called when receiving a "elev_request_add" packet. This is request
        packet from the floor panel, contains the destination floor and the
        direction.
        """

        self._join_transaction(tid)
        logging.debug("Start handling a \"elev_request_add\" packet "
                      "(floor = %d, direction = %s)",
                      data["floor"], data["direction"])

        floor = data["floor"]
        direction = data["direction"]

        logging.info("Add floor request (floor = %d, direction = %s)",
                     floor, direction)

        if direction == core.Direction.Up:
            self.__request_floors[floor].call_up = True
        else:
            self.__request_floors[floor].call_down = True

        logging.debug("Finish handling a \"elev_request_add\" packet "
                      "(floor = %d, direction = %s)", floor, direction)
        return True

    def get_current_request_list(self, tid):
        """
        Returns the current list of all requests.
        """

        self._join_transaction(tid)
        logging.debug("Start returning the current request list")

        logging.debug("Finish returning the current request list")
        return self.__request_floors

    def set_request_served(self, tid, floor, direction):
        """
        Sets the request to the specified floor and direction has been served.
        This function is called by the elevator manager when the elevator
        reaches its destination.
        """

        self._join_transaction(tid)
        logging.debug("Start setting the request as served "
                      "(floor = %d, direction = %s)", floor, direction)

        # Removes the request belongs to this floor and turns off the light
        if direction == core.Direction.Up:
            self.__request_floors[floor].call_up = False
        if direction == core.Direction.Down:
            self.__request_floors[
                floor].call_down = False

        if self.__request_floors[floor].cabin:
            logging.debug("Turns off the cabin button light")
            self.__request_floors[floor].cabin = False
            self.__user_interface.turn_button_light_off(
                tid, floor)

        # Sends request served message to the floor panel
        logging.debug("Sends the request served packet to the floor panel")
        self.__network.send_packet(
            self.__floor_address[floor],
            "floor_request_served",
            {"elevator": self.__elevator, "direction": direction})

        logging.debug("Finish setting the request as served "
                      "(floor = %d, direction = %s)", floor, direction)
