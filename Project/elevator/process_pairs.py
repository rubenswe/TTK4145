"""
Created on Feb 9, 2017

@author: Viet-Hoa Do
"""
import logging
import threading
import time


class PrimaryBackupSwitchable(object):
    """
    Supports exporting/importing the current state of the module and starting
    working from that. This interface should be applied to every modules in the
    system which uses process-pairs design.
    Attention: state of modules needs to be locked in each operation (function)
    to make sure the current state of the system is exported/imported between
    each request. 
    """

    def start(self):
        """
        Starts working from the current state. Every initialization should be
        done before calling this function, even in backup system.
        """

        raise NotImplementedError()

    def stop(self):
        """
        Stops working, but still keeping the current state. The module is now
        switched to backup mode and can import the state from other system.
        """

        raise NotImplementedError()

    def export_state(self):
        """
        Returns the current state of the module in serializable format. The
        state will be stored and shared with other system (backup) in network.
        Make sure that all the required information is included and the module
        can start working correctly only from these information.
        """

        raise NotImplementedError()

    def import_state(self, state):
        """
        Replaces the current state of the module with the specified one. This
        function is reversed version of export_state.
        """

        raise NotImplementedError()


class PrimaryBackupSwitcher(object):
    """
    Manages all the modules in the system, exchanges state between the primary
    and backup and switches the roles of the system.
    """

    __PACKET_ARE_YOU_ALIVE = "are_you_alive"
    __PACKET_I_AM_PRIMARY = "i_am_primary"

    def __init__(self):
        self.__is_primary = False
        self.__module_list = None
        self.__network = None

        self.__partner_address = None
        self.__max_attempts = 0

    def init(self, config, module_list, network):

        # Validates input data types
        assert isinstance(module_list, dict)
        for name, module in module_list.items():
            assert isinstance(name, str)
            assert isinstance(module, PrimaryBackupSwitchable)

        self.__module_list = module_list
        self.__network = network

        self.__partner_address = (config.process_pairs.partner_ip_address,
                                  config.process_pairs.partner_port)
        self.__max_attempts = config.process_pairs.max_attempts

        self.__set_primary_mode(False)
        self.__network.add_packet_handler(
            self.__PACKET_I_AM_PRIMARY, self.__on_receive_i_am_primary)

    def __on_receive_are_you_alive(self, source_addr, data):

        if not self.__is_primary:
            return False

        data = {"states": dict()}
        states = data["states"]

        # Gets the current state of all the modules
        for name, module in self.__module_list.items():
            module_state = module.export_state()
            states[name] = module_state

        # Sends back the current state
        return data

    def __on_receive_i_am_primary(self, source_addr, data):

        logging.info("[PROCESS PAIRS] Received 'I am primary' message")
        self.__set_primary_mode(False)

    def set_primary_mode(self, is_primary):
        self.__set_primary_mode(is_primary)

    def __set_primary_mode(self, is_primary):

        if is_primary:
            logging.info("[PROCESS PAIRS] Begin switching to primary mode")
        else:
            logging.info("[PROCESS PAIRS] Begin switching to backup mode")

        self.__is_primary = is_primary

        if not is_primary:  # BACKUP MODE

            # Stops all modules
            for module in self.__module_list.values():
                module.stop()
            self.__network.stop_server()

            # Monitors the primary
            thread = threading.Thread(target=self.__monitor_primary,
                                      daemon=True)
            thread.start()

        else:  # PRIMARY MODE

            # Starts the network server and waits for requests from the backup
            self.__network.add_packet_handler(
                self.__PACKET_ARE_YOU_ALIVE, self.__on_receive_are_you_alive)
            self.__network.start_server()
            self.__network.send_packet(
                self.__partner_address,
                self.__PACKET_I_AM_PRIMARY, dict())

            # Starts all modules
            for module in self.__module_list.values():
                module.start()

        if is_primary:
            logging.info("[PROCESS PAIRS] End switching to primary mode")
        else:
            logging.info("[PROCESS PAIRS] End switching to backup mode")

    def __monitor_primary(self):

        logging.warning("[PROCESS PAIRS] Begin monitoring the primary")
        is_valid = True
        attempts = 0

        while not self.__is_primary:

            # Asks the primary for its current state
            time.sleep(1)
            attempts += 1
            response = self.__network.send_packet(
                self.__partner_address,
                self.__PACKET_ARE_YOU_ALIVE, dict())

            # Validates the response
            is_valid = True

            if response is False:
                logging.warning("[PROCESS PAIRS] Primary does not response!")
                is_valid = False
            elif not isinstance(response, dict):
                logging.error(
                    "[PROCESS PAIRS] Response is not a dictionary!")
                is_valid = False
            elif "states" not in response:
                logging.error("[PROCESS PAIRS] Response does not contain "
                              "current modules state!")
                is_valid = False
            else:
                states = response["states"]

                # Saves the current state of the primary to all the modules
                for name, module in self.__module_list.items():
                    if name in states:
                        module.import_state(states[name])
                    else:
                        logging.error(
                            "[PROCESS PAIRS] The state of module '%s'"
                            " is not found!" % (name))
                        is_valid = False

            if is_valid:
                attempts = 0
            elif attempts >= self.__max_attempts:
                logging.info("[PROCESS PAIRS] Switch to primary mode")
                self.__set_primary_mode(True)
                break

        logging.info("End monitoring the primary")

    def destroy(self):
        pass
