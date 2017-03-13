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
import core
import transaction


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

    def export_state(self, tid):
        """
        Returns the current state of the module in serializable format. The
        state will be stored and shared with other system (backup) in network.
        Make sure that all the required information is included and the module
        can start working correctly only from these information.
        """

        raise NotImplementedError()

    def import_state(self, tid, state):
        """
        Replaces the current state of the module with the specified one. This
        function is reversed version of export_state.
        """

        raise NotImplementedError()


class ProcessPair(object):
    """
    Establishes process pairs fault tolerance mechanism for set of modules
    in system.
    These modules must implement the process_pairs.PrimaryBackupSwitchable
    interface which provides the ability for process pair module to activate
    the modules when the process is in primary mode and export/import the
    current internal state of each module gradually.

    Usage: pp = ProcessPair(config, arguments)
        - config: system configuration reader
        - arguments: command line argument list (produced by argparse)

    Required configuration:
        - process_pairs.address: IPC channel address for primary/backup
          communication. It can be TCP/IP address, UNIX socket (*nix only)
          or Pipe name (Windows only).
        - process_pairs.period: state sending period in seconds (float)
    """

    def __init__(self):
        self.__enabled = True

        self.__is_primary = False
        self.__module_list = None

        self.__config = None
        self.__arguments = None

        self.__address = None
        self.__period = None

        self.__is_channel_created = None

    def init(self, config, transaction_manager, arguments):
        """
        Initializes the process pairs controller.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)

        self.__config = config
        self.__transaction_manager = transaction_manager
        self.__arguments = arguments

    def start(self, module_list):
        """
        Starts process pairs fault tolerance mechanism. The internal state
        of the specified set of modules will be exchanged between primary
        and backup processes.

        When the current process is in primary mode, all the modules will be
        activated.

        @param module_list: list of name/value pairs, e.g:
                            {
                                "network": network_module,
                                "motor": motor_module,
                            }
        """

        logging.debug("Start activating process pairs mechanism")

        self.__enabled = self.__config.get_int("process_pairs", "enabled") == 1

        self.__module_list = module_list

        # Reads the configuration
        self.__address = (
            self.__config.get_value("process_pairs", "ip_address"),
            self.__config.get_int("process_pairs", "port"))
        self.__period = self.__config.get_float("process_pairs", "period")

        # Reads the operation mode from the command line argument
        is_primary = not self.__arguments.mode == "backup"

        # Switches the system to that mode
        self.__set_primary_backup(is_primary)

        logging.debug("Finish activating process pairs mechanism")

    @staticmethod
    def __create_backup_process():
        """
        Creates new independent process running in backup mode.
        """

        # All the program and arguments are the same, except the running mode
        args = [sys.executable]
        args.extend(sys.argv)
        if "--mode=backup" not in args:
            args.append("--mode=backup")

        # Starts new independent process
        subprocess.Popen(args)

    def __set_primary_backup(self, is_primary):
        """
        Sets the operation mode of the system.
        Note: it is designed to be able to switch from backup mode to primary
              mode, but not the other way around.
        """

        self.__is_primary = is_primary

        if is_primary:
            logging.info("Start switching to primary mode")
        else:
            logging.info("Start switching to backup mode")

        if self.__enabled:
            if is_primary:

                # Starts all the modules
                logging.debug("Activate all modules")
                for module in self.__module_list.values():
                    module.start()

                # Creates new thread to open a connection with the backup
                # to periodically send state as well as monitor the backup.
                #
                # Ensures that the communication channel has been created
                # before creating a backup process.
                logging.debug("Start a primary mode monitoring thread")
                thread = threading.Thread(
                    target=self.__primary_mode_thread, daemon=True)

                self.__is_channel_created = False
                thread.start()
                while not self.__is_channel_created:
                    continue

                # Creates backup process
                logging.debug("Create a backup process")
                self.__create_backup_process()

            else:

                # Starts a thread to monitor how old the last backup is
                logging.debug("Start a backup mode monitoring thread")
                thread = threading.Thread(target=self.__backup_mode_thread,
                                          daemon=True)
                thread.start()
        else:  # Process pairs mechanism is disabled
            logging.debug("Process pairs mechanism is disabled")

            if is_primary:
                logging.debug("Activate all modules")
                for module in self.__module_list.values():
                    module.start()

        if is_primary:
            logging.debug("Finish switching to primary mode")
        else:
            logging.debug("Finish switching to backup mode")

    def __primary_mode_thread(self):
        """
        Primary mode monitoring thread which periodically sends the current
        state to the backup process. It also creates a new backup process
        if the connection has lost.
        """

        while True:
            logging.debug("Open a connection with the backup")
            with Listener(self.__address) as listener:
                self.__is_channel_created = True

                try:
                    logging.debug("Wait for the backup")
                    with listener.accept() as conn:
                        logging.info("The backup is connected")

                        while self.__is_primary:
                            # Gets the current state of the system
                            logging.debug(
                                "Get the current state of all modules")

                            tid = self.__transaction_manager.start()
                            states = {name: module.export_state(tid)
                                      for (name, module) in
                                      self.__module_list.items()}
                            self.__transaction_manager.finish(tid)

                            # Sends to the backup and waits for acknowledgement
                            logging.debug("Send state to the backup")
                            conn.send(states)

                            logging.debug("Wait for ACK from the backup")
                            _ = conn.recv()

                            # Sleep
                            time.sleep(self.__period)

                except (ConnectionResetError, BrokenPipeError, EOFError):
                    logging.error("Connection with the backup is down. "
                                  "The backup has been able to crash!")

                # Tries to create the backup again
                self.__create_backup_process()

    def __backup_mode_thread(self):
        """
        Backup mode monitoring thread which receives the current state
        of the primary process. When the connection has lost, the system
        will be switched to primary mode.
        """

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

                    tid = self.__transaction_manager.start()
                    for (name, module) in self.__module_list.items():
                        module.import_state(tid, states[name])
                    self.__transaction_manager.finish(tid)

                    # Sends acknowledgement
                    logging.debug("Send ACK to the primary")
                    conn.send(True)
        except (ConnectionResetError, BrokenPipeError, EOFError):
            logging.error("Connection with the primary is down. The primary "
                          "has been able to crash!")

        # Switches to primary mode
        self.__set_primary_backup(True)
