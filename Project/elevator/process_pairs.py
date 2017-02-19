"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import threading
import time
import subprocess
import sys
from multiprocessing.connection import Listener, Client


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

        self.__address = None
        self.__authkey = None

        self.__max_attempts = 0

        self.__period = 0.0
        self.__timeout = 0.0

        self.__last_backup = None

    def init(self, config, is_primary, module_list):

        self.__module_list = module_list

        self.__address = config.get_value("process_pairs", "address")
        self.__authkey = config.get_value("process_pairs", "authkey")

        self.__max_attempts = config.get_int("process_pairs", "max_attempts")

        self.__period = config.get_float("process_pairs", "period")
        self.__timeout = config.get_float("process_pairs", "timeout")

        self.__set_primary_backup(is_primary)

    def __create_backup_process(self):

        args = [sys.executable]
        args.extend(sys.argv)
        if "--mode=backup" not in args:
            args.append("--mode=backup")
        print(args)
        subprocess.Popen(args)

    def __set_primary_backup(self, is_primary):
        self.__is_primary = is_primary
        if is_primary:
            logging.info("Start primary mode")
        else:
            logging.info("Start backup mode")

        if is_primary:

            # Starts all the modules
            for module in self.__module_list.values():
                module.start()

            # Creates new thread to open a connection with the backup
            # to periodically send state as well as monitor the backup
            thread = threading.Thread(
                target=self.__primary_mode_thread, daemon=True)
            thread.start()

            # Creates backup process
            self.__create_backup_process()

        else:

            self.__last_backup = time.time()

            # Starts a thread to monitor how old the last backup is
            thread = threading.Thread(target=self.__backup_mode_thread,
                                      daemon=True)
            thread.start()

    def __primary_mode_thread(self):

        while True:
            try:
                logging.debug("Open a connection with the backup")
                with Listener(self.__address) as listener:

                    logging.debug("Wait for the backup")
                    with listener.accept() as conn:
                        logging.info("The backup is connected")

                        while self.__is_primary:
                            # Gets the current state of the system
                            logging.debug(
                                "Get the current state of all modules")

                            states = {name: module.export_state()
                                      for (name, module) in
                                      self.__module_list.items()}

                            # Sends to the backup and waits for acknowledgement
                            logging.debug("Send state to the backup")
                            conn.send(states)

                            logging.debug("Wait for ACK from the backup")
                            _ = conn.recv()

                            # Sleep
                            time.sleep(self.__period)

            except (ConnectionResetError, BrokenPipeError, EOFError):
                logging.error("Connection with the backup is down. The backup "
                              "has been able to crash!")

            # Tries to create the backup again
            self.__create_backup_process()

    def __on_backup_received_state(self, address, data):

        self.__last_backup = time.time()
        states = data["states"]

        for (name, module) in self.__module_list.items():
            module.import_state(states[name])

        return True

    def __backup_mode_thread(self):

        try:
            logging.debug("Connect to the primary")
            with Client(self.__address) as conn:
                logging.info("Connected to the primary")

                while True:
                    # Waits for the current state from the primary
                    logging.debug("Wait for state from the primary")
                    states = conn.recv()

                    # Imports the received state
                    logging.debug(
                        "Import the current state of primary to backup")
                    for (name, module) in self.__module_list.items():
                        module.import_state(states[name])

                    # Sends acknowledgement
                    logging.debug("Send ACK to the primary")
                    conn.send(True)
        except (ConnectionResetError, BrokenPipeError, EOFError):
            logging.error("Connection with the primary is down. The primary "
                          "has been able to crash!")

        # Switches to primary mode
        self.__set_primary_backup(True)
