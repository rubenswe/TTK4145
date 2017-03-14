import logging
import threading
import time
import driver
import core
import transaction
import floor_panel
import module_base


class UserInterface(module_base.ModuleBase):
    """
    Provides user interacting interface, including:
        - Up/Down button
        - Up/Down light
    """

    def __init__(self):
        module_base.ModuleBase.__init__(self)

        # Related modules
        self.__transaction_manager = None
        self.__driver = None
        self.__request_manager = None

        # Configurations
        self.__floor = 0
        self.__period = 0.0

        # States
        self.__started = False

        self.__light_up = False  # Whether the up button light is on
        self.__light_down = False  # Whether the down button light is on

    def init(self, config, transaction_manager, _driver, request_manager):
        """
        Initializes the user interface for floor panel.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)
        assert isinstance(_driver, driver.Driver)
        assert isinstance(request_manager,
                          floor_panel.request_manager.RequestManager)

        logging.debug("Start initializing user interface module")
        module_base.ModuleBase.init(self, transaction_manager)

        self.__transaction_manager = transaction_manager
        self.__driver = _driver
        self.__request_manager = request_manager

        # Reads the configuration
        self.__floor = config.get_int("floor", "floor")
        self.__period = config.get_float("floor", "ui_monitor_period", 0.1)

        logging.debug("Finish initializing user interface module")

    def start(self, tid):
        """
        Starts working from the current state.
        """

        self._join_transaction(tid)
        logging.debug("Start activating user interface module")

        self.__started = True

        # Starts button monitoring thread
        logging.debug("Start button monitoring thread")
        threading.Thread(
            target=self.__button_monitor_thread, daemon=True).start()

        logging.debug("Finish activating user interface module")

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format.
        """

        self._join_transaction(tid)
        logging.debug("Start exporting current state of user interface")

        state = {
            "light_up": self.__light_up,
            "light_down": self.__light_down,
        }

        logging.debug("Finish exporting current state of user interface")
        return state

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one.
        """

        self._join_transaction(tid)
        logging.debug("Start importing current state of user interface")

        self.__light_up = state["light_up"]
        self.__light_down = state["light_down"]

        logging.debug("Finish importing current state of user interface")

    def prepare_to_commit(self, tid):
        """
        Before committing, updates the button lights to make sure that
        the button lights can only be changed when the transaction is success.
        """

        self._join_transaction(tid)
        self.__update_button_light(tid)

        return module_base.ModuleBase.prepare_to_commit(self, tid)

    def __update_button_light(self, tid):
        """
        Turns button lights on/off. This function should be called at the end
        of a transaction to make sure that the button indicators are only
        changed when a transaction is ok.
        """

        self._join_transaction(tid)
        logging.debug("Start updating the button lights")

        if self.__light_up:
            self.__driver.set_button_lamp(
                driver.FloorButton.CallUp, self.__floor, 1)
        else:
            self.__driver.set_button_lamp(
                driver.FloorButton.CallUp, self.__floor, 0)

        if self.__light_down:
            self.__driver.set_button_lamp(
                driver.FloorButton.CallDown, self.__floor, 1)
        else:
            self.__driver.set_button_lamp(
                driver.FloorButton.CallDown, self.__floor, 0)

        logging.debug("Finish updating the button lights")

    def turn_button_light_off(self, tid, direction):
        """
        Turns off the direction button light.
        """

        self._join_transaction(tid)
        logging.info(
            "Start turning the button light off (direction = %s)", direction)

        if direction == core.Direction.Up:
            self.__light_up = False
        else:
            self.__light_down = False

        # Not turns of the light yet, wait for commit

        logging.debug(
            "Finish turning the button light off (direction = %s)", direction)

    def __button_monitor_thread(self):
        """
        Periodically checks whether button is pushed.
        """

        logging.debug("Start monitoring floor panel button")

        is_pushed = {
            driver.FloorButton.CallUp: 0,
            driver.FloorButton.CallDown: 0,
        }

        while True:

            # Checks each button (up, down, command). If any of them is pushed,
            # sends request to the request manager
            for button in is_pushed:
                value = self.__driver.get_button_signal(button, self.__floor)
                if is_pushed[button] == 0 and value == 1:
                    # This button is pushed

                    logging.debug("Floor %d, button %d is pushed",
                                  self.__floor, button)

                    tid = self.__transaction_manager.start()
                    self._join_transaction(tid)

                    if button == driver.FloorButton.CallUp:
                        direction = core.Direction.Up
                        self.__light_up = True
                    if button == driver.FloorButton.CallDown:
                        direction = core.Direction.Down
                        self.__light_down = True

                    # Sends request to request manager
                    logging.debug("Send request to the request manager")
                    self.__request_manager.add_request(tid, direction)

                    self.__transaction_manager.finish(tid)

                is_pushed[button] = value

            time.sleep(self.__period)

        # This function never end
