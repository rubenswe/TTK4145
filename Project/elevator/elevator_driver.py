from ctypes import cdll
from configparser import ConfigParser
from enum import IntEnum
import logging
from common import Config, Direction
import threading

native = cdll.LoadLibrary(
    "../elevator_driver_native/Release/libelevator_driver_native.so")


class DriverType(IntEnum):

    Comedi = 0,
    Simulation = 1


class DriverConfig(object):

    def __init__(self, reader):
        assert isinstance(reader, ConfigParser)
        logging.debug("Begin reading the driver configuration")

        self.floors = int(reader.get("system", "floors"))

        # Gets the driver type (using hardware via comedi or using simulation)
        type_name = reader.get("driver", "type")

        if type_name.lower() == "comedi":
            self.driver_type = DriverType.Comedi
        elif type_name.lower() == "simulation":
            self.driver_type = DriverType.Simulation
        else:
            logging.fatal("Driver type has not been specified!")
            raise RuntimeError()

        # Gets simulation server address for simulation mode
        if self.driver_type == DriverType.Simulation:
            self.ip_address = reader.get("driver", "ip_addr")
            self.port = reader.get("driver", "port")

        logging.debug("End reading the driver configuration")


class Driver(object):

    def __init__(self, config):
        assert isinstance(config, Config)
        logging.debug("Begin initializing the driver")

        self.config = DriverConfig(config.reader)
        self.running = True

        native.elev_init(self.config.driver_type)

        # Goes to the first floor
        self.position = self.config.floors - 1
        self.direction = Direction.Down
        self.target = 0

        self.control_thread = threading.Thread(target=self.control_proc)
        self.control_thread.start()
        while self.direction != Direction.Stop:
            continue

        logging.debug("End initializing the driver")

    def change_floor(self, num):
        assert isinstance(num, int)
        assert num >= 0 and num < self.config.floors
        logging.debug("Begin changing the destination floor")

        self.target = num

        logging.debug("End changing the destination floor")

    def control_proc(self):
        logging.debug("Begin elevator controlling")

        while self.running:
            sensor_pos = native.elev_get_floor_sensor_signal()
            if sensor_pos >= 0:
                self.position = sensor_pos

            if self.position > self.target:
                self.direction = Direction.Down
            elif self.position < self.target:
                self.direction = Direction.Up
            else:
                self.direction = Direction.Stop

            native.elev_set_motor_direction(self.direction)

        native.elev_set_motor_direction(Direction.Stop)

        logging.debug("End elevator controlling")

    def __del__(self):
        self.running = False


def main():
    native.elev_init(0)
    native.elev_set_button_lamp(0, 1, 1)
    input("aaa")
    native.elev_set_button_lamp(0, 1, 0)


if __name__ == "__main__":
    main()
