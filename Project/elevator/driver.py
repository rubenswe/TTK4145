import logging
import socket
import threading
import ctypes
import enum
import module_base
import core
import transaction


class DriverTarget(enum.IntEnum):
    """
    Hardware or simulator.
    """

    Comedi = 0,
    Simulation = 1


class MotorDirection(enum.IntEnum):

    Down = -1
    Stop = 0
    Up = 1


class FloorButton(enum.IntEnum):

    CallUp = 0
    CallDown = 1
    Command = 2


class Driver(module_base.ModuleBase):
    """
    Provides functionalities to interact with hardware components, including:
        - Floor panels buttons and lights
        - An elevator panel buttons and lights
        - An elevator motor and sensors
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        self.__type = None
        self.__address = None
        self.__lib = None

    def init(self, config, transaction_manager):
        """
        Initializes the driver module.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)

        module_base.ModuleBase.init(self, transaction_manager)

        # Gets the driver target (hardware or simulation)
        self.__type = DriverTarget.Simulation
        if config.get_value("driver", "type") == "Comedi":
            self.__type = DriverTarget.Comedi

        if self.__type == DriverTarget.Simulation:
            self.__address = (
                config.get_value("driver", "ip_address"),
                config.get_int("driver", "port"))

            self.__lib = SimulationDriver()
        else:
            self.__address = None
            self.__lib = ctypes.cdll.LoadLibrary(
                "../../driver/libdriver.so")

    def start(self, tid):
        """
        Starts working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start activating driver module")

        if self.__type == DriverTarget.Simulation:
            self.__lib.elev_init(self.__address[0], self.__address[1])
        else:
            self.__lib.elev_init()

        # Sets the stop button light to 0 to detect the motor box power off
        self.__lib.elev_set_stop_lamp(0)

        logging.debug("Finish activating driver module")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        logging.debug("Start exporting current state of driver")
        logging.debug("Finish exporting current state of driver")

        return dict()

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        logging.debug("Start importing current state of driver")
        logging.debug("Finish importing current state of driver")

    def set_motor_direction(self, direction):
        self.__lib.elev_set_motor_direction(direction)

    def set_button_lamp(self, button, floor, value):
        self.__lib.elev_set_button_lamp(button, floor, value)

    def set_floor_indicator(self, floor):
        self.__lib.elev_set_floor_indicator(floor)

    def set_door_open_lamp(self, value):
        self.__lib.elev_set_door_open_lamp(value)

    def set_stop_lamp(self, value):
        self.__lib.elev_set_stop_lamp(value)

    def get_button_signal(self, button, floor):
        if self.__lib.elev_get_stop_signal() != 0:
            # The motor box has lost of power, returns a "safe" value
            return 0

        return self.__lib.elev_get_button_signal(button, floor)

    def get_floor_sensor_signal(self):
        if self.__lib.elev_get_stop_signal() != 0:
            # The motor box has lost of power, returns a "safe" value
            return -1

        return self.__lib.elev_get_floor_sensor_signal()

    def get_stop_signal(self):
        if self.__lib.elev_get_stop_signal() != 0:
            # The motor box has lost of power, returns a "safe" value
            return 0

        return self.__lib.elev_get_stop_signal()

    def get_obstruction_signal(self):
        if self.__lib.elev_get_stop_signal() != 0:
            # The motor box has lost of power, returns a "safe" value
            return 0

        return self.__lib.elev_get_obstruction_signal()


class SimulationDriver(object):
    """
    Network-based elevator simulator driver which is rewritten from the native
    driver provided to support platform-independence.
    """

    def __init__(self):

        self.__socket = None
        self.__socket_lock = threading.Lock()

    def elev_init(self, ip_addr, port):
        """
        Starts working from the current state.
        """

        self.__socket_lock.acquire()

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.connect((ip_addr, port))

        self.__socket_lock.release()

    def __sync_send(self, msg, receive=False):
        self.__socket_lock.acquire()

        self.__socket.send(msg)
        if receive:
            recv = self.__socket.recv(1024)
        else:
            recv = None

        self.__socket_lock.release()

        return recv

    def __sync_send_and_receive(self, msg):
        return self.__sync_send(msg, True)

    def elev_set_motor_direction(self, direction):
        msg = bytearray([1, (direction + 256) % 256, 0, 0])
        self.__sync_send(msg)

    def elev_set_button_lamp(self, button, floor, value):
        msg = bytes([2, button, floor, value])
        self.__sync_send(msg)

    def elev_set_floor_indicator(self, floor):
        msg = bytes([3, floor, 0, 0])
        self.__sync_send(msg)

    def elev_set_door_open_lamp(self, value):
        msg = bytes([4, value, 0, 0])
        self.__sync_send(msg)

    def elev_set_stop_lamp(self, value):
        msg = bytes([5, value, 0, 0])
        self.__sync_send(msg)

    def elev_get_button_signal(self, button, floor):
        msg = bytes([6, button, floor, 0])
        resp = self.__sync_send_and_receive(msg)
        return resp[1]

    def elev_get_floor_sensor_signal(self):
        msg = bytes([7, 0, 0, 0])
        resp = self.__sync_send_and_receive(msg)

        if resp[1] != 0:
            return resp[2]
        return -1

    def elev_get_stop_signal(self):
        msg = bytes([8, 0, 0, 0])
        resp = self.__sync_send_and_receive(msg)
        return resp[1]

    def elev_get_obstruction_signal(self):
        msg = bytes([9, 0, 0, 0])
        resp = self.__sync_send_and_receive(msg)
        return resp[1]
