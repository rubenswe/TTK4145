"""
Created on Feb 9, 2017

@author: Viet-Hoa Do
"""
import logging
import threading
import time
import inspect
import subprocess
import sys


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


class ProcessPair(object):

    CURRENT_STATE_PACKET = "process_pair_current_state"

    def __init__(self):
        self.__is_primary = False
        self.__module_list = None
        self.__network = None

        self.__partner_address = None
        self.__max_attempts = 0

        self.__period = 0.0
        self.__timeout = 0.0

        self.__last_backup = None

    def init(self, config, module_list, network, is_primary):

        # Validates input data types
        assert isinstance(module_list, dict)
        for name, module in module_list.items():
            assert isinstance(name, str)
            assert isinstance(module, PrimaryBackupSwitchable)

        self.__module_list = module_list
        self.__network = network
        self.__network.add_packet_handler(self.CURRENT_STATE_PACKET,
                                          self.__on_backup_received_state)

        self.__primary_address = (config.network.ip_address,
                                  config.network.port)
        self.__partner_address = (config.process_pairs.partner_ip_address,
                                  config.process_pairs.partner_port)
        self.__max_attempts = config.process_pairs.max_attempts

        self.__period = config.process_pairs.period
        self.__timeout = config.process_pairs.timeout

        self.__set_primary_backup(is_primary)

    def __create_backup_process(self):

        args = ["python3"]
        args.extend(sys.argv)
        if "--mode=backup" not in args:
            args.append("--mode=backup")
        print(args)
        subprocess.Popen(args)

    def __set_primary_backup(self, is_primary):
        self.__is_primary = is_primary
        if is_primary:
            logging.info("[PROCESS PAIRS] Start primary mode")
        else:
            logging.info("[PROCESS PAIRS] Start backup mode")

        if is_primary:

            # Starts the network server in primary mode
            self.__network.start_server(self.__primary_address)

            # Creates backup process
            self.__create_backup_process()

            # Creates new thread to periodically send state
            thread = threading.Thread(
                target=self.__send_state_thread, daemon=True)
            thread.start()

            # Starts all the modules
            for module in self.__module_list.values():
                module.start()

        else:

            self.__last_backup = time.time()

            # Starts the network server in backup mode
            self.__network.start_server(self.__partner_address)

            # Starts a thread to monitor how old the last backup is
            thread = threading.Thread(target=self.__backup_monitor,
                                      daemon=True)
            thread.start()

    def __send_state_thread(self):

        attempts = 0

        while self.__is_primary:

            # Sleep
            time.sleep(self.__period)

            # Gets the current state of the system
            states = dict()
            for (name, module) in self.__module_list.items():
                states[name] = module.export_state()

            # Sends the current state to the backup
            attempts += 1
            resp = self.__network.send_packet(self.__partner_address,
                                              self.CURRENT_STATE_PACKET,
                                              {"states": states})
            if resp is True:
                attempts = 0
            elif attempts >= self.__max_attempts:
                # The backup has been dead
                self.__create_backup_process()

    def __on_backup_received_state(self, address, data):

        self.__last_backup = time.time()
        states = data["states"]

        for (name, module) in self.__module_list.items():
            module.import_state(states[name])

        return True

    def __backup_monitor(self):

        while not self.__is_primary:
            now = time.time()
            period = now - self.__last_backup

            if period > self.__timeout:
                self.__set_primary_backup(True)
                return
