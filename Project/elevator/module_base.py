"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import threading
import copy
import process_pairs
import transaction


class ModuleBase(process_pairs.PrimaryBackupSwitchable,
                 transaction.ResourceManager):
    """
    Base class for all the modules in the system. Two main mechanisms used
    in the system are:
      - Process pairs fault tolerance
      - Transaction-based backward recovery
    """

    def __init__(self):
        self.__transaction_manager = None
        self.__transaction_id = None
        self.__resource_lock = threading.Lock()

        self.__prev_state = None
        self.__can_commit = True

    def init(self, transaction_manager):
        """
        Initializes the base module functionalities.
        """

        assert isinstance(transaction_manager, transaction.TransactionManager)
        logging.debug("Start initializing the base module functionalities")

        self.__transaction_manager = transaction_manager

        logging.debug("Finish initializing the base module functionalities")

    def _join_transaction(self, tid):
        """
        Joins the specified transaction. A resource manager can only join one
        transaction at the same time.
        """

        if self.__transaction_id is None or self.__transaction_id != tid:
            # Joins the transaction
            self.__resource_lock.acquire()

            self.__transaction_manager.join(tid, self)

            self.__transaction_id = tid
            self.__prev_state = copy.deepcopy(self.export_state(tid))
            self.__can_commit = True

    def _get_can_commit(self, tid):
        """
        Gets whether the specified transaction can commit.
        """

        self._join_transaction(tid)
        return self.__can_commit

    def _set_can_commit(self, tid, can_commit):
        """
        Sets whether the specified transaction can commit.
        """

        self._join_transaction(tid)
        self.__can_commit = can_commit

    def _leave_transaction(self, tid):
        """
        Leaves the specified transaction after commit/abort.
        """

        assert tid == self.__transaction_id

        self.__transaction_id = None
        self.__resource_lock.release()

    def prepare_to_commit(self, tid):
        """
        Returns whether the specified transaction is ok or not.
        """

        self._join_transaction(tid)
        return self.__can_commit

    def commit(self, tid):
        """
        Keeps the new state of the module and unlocks the resources.
        """

        self._join_transaction(tid)
        logging.debug("Start committing the transaction (tid = %s)", tid)

        logging.debug("Finish commit the transaction (tid = %s)", tid)
        self._leave_transaction(tid)

    def abort(self, tid):
        """
        Restores the previous state of the module and unlocks the resources.
        """

        self._join_transaction(tid)
        logging.debug("Start aborting the transaction (tid = %s)", tid)

        # Recovers the old state and resets the commit flag
        self.import_state(tid, self.__prev_state)

        logging.debug("Finish aborting the transaction (tid = %s)", tid)
        self._leave_transaction(tid)
