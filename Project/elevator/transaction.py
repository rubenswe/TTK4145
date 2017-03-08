"""
Copyright (c) 2017 Viet-Hoa Do <viethoad[at]stud.ntnu.com>
              2017 Ruben Svendsen Wedul <rubensw[at]stud.ntnu.no>
All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import uuid
import threading


class TransactionManager(object):
    """
    Supports two-phase commit transaction for all actions in the system.
    """

    def __init__(self):
        self.__lock = threading.Lock()
        self.__transaction_list = dict()

    def start(self):
        """
        Starts new transaction, returns the new transaction identifier.
        """

        self.__lock.acquire()
        logging.debug("Start creating new transaction")

        # Generates a unique transaction identifier
        while True:
            new_id = uuid.uuid4()
            if new_id not in self.__transaction_list:
                break

        # Adds the transaction to the list
        logging.debug("New transaction identifier: %s", str(new_id))
        self.__transaction_list[new_id] = Transaction(new_id)

        logging.debug("Finish creating new transaction")
        self.__lock.release()

        return new_id

    def join(self, tid, resource):
        """
        Adds the specified resource manager to the transaction.
        """

        assert isinstance(resource, ResourceManager)

        self.__lock.acquire()
        logging.debug(
            "Start adding resource to transaction (tid = %s, resource = %s)",
            tid, type(resource))

        if tid in self.__transaction_list:
            self.__transaction_list[tid].resources.add(resource)
        else:
            logging.error("Transaction not found! (tid = %s)", tid)

        logging.debug(
            "Finish adding resource to transaction (tid = %s, resource = %s)",
            tid, type(resource))
        self.__lock.release()

    def finish(self, tid):
        """
        Finishes the specified transaction. If all actions have been done
        successfully, commits all resources and return True. Otherwise,
        aborts the transaction and return False.
        """

        can_commit = True

        self.__lock.acquire()
        logging.debug("Start ending transaction (tid = %s)", tid)

        if tid in self.__transaction_list:

            transaction = self.__transaction_list[tid]

            # Asks all resource managers whether this transaction
            # can be committed or not
            logging.debug(
                "Call all resources preparing to commit (tid = %s)", tid)
            for resource in transaction.resources:
                if not resource.prepare_to_commit(tid):
                    can_commit = False
                    break  # No need to ask any other

            # Commits/aborts the transaction
            if can_commit:
                logging.debug("Commit the transaction (tid = %s)", tid)
                for resource in transaction.resources:
                    resource.commit(tid)
            else:
                logging.debug("Abort the transaction (tid = %s)", tid)
                for resource in transaction.resources:
                    resource.abort(tid)

        else:
            logging.error("Transaction not found! (tid = %s)", tid)

        logging.debug("Finish ending transaction (tid = %s)", tid)
        self.__lock.release()

        return can_commit


class Transaction(object):
    """
    Transaction information including unique identifier and list of joint
    resource managers.
    """

    def __init__(self, tid):

        # All data are public and directly accessible by transaction manager
        self.tid = tid
        self.resources = set()


class ResourceManager(object):
    """
    Supports doing task under two-phase commit transaction.
    """

    def __init__(self, transaction_manager):
        self.__transaction_manager = transaction_manager
        self.__transaction_id = None
        self.__resource_lock = threading.Lock()

    def join_transaction(self, tid):
        """
        Joins the specified transaction. A resource manager can only join one
        transaction at the same time.
        """

        if self.__transaction_id is None or self.__transaction_id != tid:
            # Joins the transaction
            self.__resource_lock.acquire()

            self.__transaction_manager.join(tid, self)
            self.__transaction_id = tid

    def leave_transaction(self, tid):
        """
        Leaves the specified transaction after commit/abort.
        """

        assert tid == self.__transaction_id

        self.__transaction_id = None
        self.__resource_lock.release()

    def prepare_to_commit(self, tid):
        """
        Returns True if the task under the specified transaction has been
        done successfully, otherwise returns False.
        """

        raise NotImplementedError()

    def commit(self, tid):
        """
        Called when the specified transaction has been done successfully.
        Commits the transaction. Call `leave_transaction` at the end
        to release the resource lock.
        """

        raise NotImplementedError()

    def abort(self, tid):
        """
        Called when the specified transaction cannot be committed due to error.
        Rollbacks the transaction. Call `leave_transaction` at the end
        to release the resource lock.
        """

        raise NotImplementedError()