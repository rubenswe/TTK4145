import logging
import common
import elevator_driver as driver


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


def main():
    logging.info("Starting elevator program...")

    # Reads the configuration
    config = common.Config("config/elevator-0.conf")

    # Initializes all modules
    _driver = driver.Driver(config)

    while True:
        s = input("Floor (0-3) (or exit): ")

        if s == "exit":
            break
        try:
            floor = int(s)
            _driver.change_floor(floor)
        except ValueError:
            continue

    logging.info("End program")


if __name__ == "__main__":
    main()
