import logging
import copy
import process_pairs
import transaction
import network
import core
from elevator import user_interface


class RequestManagerState(object):
    """
    Internal state of the request manager module. For reducing complexity,
    all fields are public and directly accessible by the UserInterface class.
    """

    def __init__(self):
        # Destination floor request is waiting to be served
        self.has_request = {}


class RequestManager(process_pairs.PrimaryBackupSwitchable):
    """
    Receives user requests from the interface++
    """

    def __init__(self, config):
        assert isinstance(config, core.Configuration)
        # assert isinstance(transaction_manager, transaction.TransactionManager)
        # assert isinstance(_network, network.Network)

        # transaction.ResourceManager.__init__(self, transaction_manager)

    def init(self, user_interface):
        pass

    def start(self):
        """
         Starts working from the current state
        """
        pass

    def export_state(self):
        """
        Returns the current state of the module in serializable format
        """
        data = {}
        return data

    def import_state(self, state):
        """
         Replaces the current state of the module in serializable format
        """
        pass

    def prepare_to_commit(self, tid):
        """
        Returns whether the specified transaction is ok or not
        """
        # return self.__can_commit
        pass

    def commit(self, tid):
        """
        Keeps the new state of the module and unlocks the resources
        """
        pass

    def abort(self, tid):
        """
        Restores the previous state of the module and unlocks the resources
        """
        pass

    # TODO: add TransactionManager, def add_request(self, tid, floor):
    def add_request(self, floor):
        """
        Adds a new request from users.
        """

        logging.debug("An request has been added! Target floor: {}".format(floor))
