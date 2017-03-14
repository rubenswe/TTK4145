import logging
import socket
import json
import threading
import time
import process_pairs
import transaction
import core


class Network(process_pairs.PrimaryBackupSwitchable):
    """
    Network module which provides a gateway to communicate with other nodes
    in the system. It allows all other modules send data packet as well as
    register their incoming packet handlers.

    All the packets have packet type which determines the type of content
    and which packet handler network module would "forward" to.

    JSON-encoded packet format:
        {
          "type": "packet type",
          "data": packet_data
        }
    """

    def __init__(self):

        # Related modules
        self.__transaction_manager = None

        # Configurations
        self.__address = None
        self.__timeout = 0.0
        self.__buffer_size = 0

        # States
        self.__handler_list = dict()

        self.__server = None

    def init(self, config, transaction_manager):
        """
        Initializes the network module.
        """

        assert isinstance(config, core.Configuration)
        assert isinstance(transaction_manager, transaction.TransactionManager)

        logging.debug("Start initializing network module")

        # Related modules
        self.__transaction_manager = transaction_manager

        # Configurations
        self.__address = (
            config.get_value("network", "ip_address", "127.0.0.1"),
            config.get_int("network", "port")
        )

        self.__timeout = config.get_float("network", "timeout", 0.5)
        self.__buffer_size = config.get_int("network", "buffer_size", 1024)

        logging.debug("Finish initializing network module")

    def start(self, tid):
        """
        Opens a UDP server and listens to incoming packets.
        """

        logging.debug("Start activating UDP server (address = %s:%d)",
                      self.__address[0], self.__address[1])

        # Opens a socket
        logging.debug("Open a UDP socket")
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            try:
                self.__server.bind(("", self.__address[1]))
                break
            except OSError:
                logging.error("Socket cannot bind the address "
                              "(address = %s:%d) => Retry",
                              self.__address[0], self.__address[1])

                time.sleep(1)
                continue

        # Starts listening to incoming packets
        logging.debug("Create new thread to listen to incoming packets")
        listening = threading.Thread(
            target=self.__server_listening_thread, daemon=True)
        listening.start()

        logging.debug("Finish activating UDP server")

    def export_state(self, tid):
        """
        Implements process_pairs.PrimaryBackupSwitchable interface.
        This module doesn't have any internal state.
        """
        return dict()

    def import_state(self, tid, state):
        """
        Implements the process_pairs.PrimaryBackupSwitchable interface.
        This module doesn't have any internal state.
        """
        pass

    def add_packet_handler(self, packet_type, handler_func):
        """
        Registers the specified packet handler function to handle all the
        incoming packets with the specified packet type.
        """

        logging.debug("Start adding packet handler (packet_type = \"%s\", "
                      "handler_func = \"%s\"", packet_type, handler_func)

        self.__handler_list[packet_type] = handler_func

        logging.debug("Finish adding packet handler")

    def send_packet(self, addr, packet_type, data):
        """
        Sends the packet to other node. The packet includes data as well as
        the packet type value which allows the receiver determines which
        module handles this packet.

        If the receiver successfully receives the packet and then replies,
        returns the response data. If not, returns False.

        Note:
            - The receiver must reply the packet, even just answers "1".
            - Anything wrong (timeout, lost connection, no reply) is considered
              failed and returns False.
        """

        logging.debug(
            "Start sending packet (addr = %s:%d, packet_type = \"%s\")",
            addr[0], addr[1], packet_type)

        # Encodes the data to sent
        packet = {"type": packet_type, "data": data}
        packet_json = json.dumps(packet)

        # Sends the packet
        logging.debug("Open a UDP socket to send packet")
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(self.__timeout)

        try:
            client.sendto(packet_json.encode(), addr)
        except OSError:
            logging.error(
                "Cannot send the packet! (addr = %s:%d, packet_type = \"%s\")",
                addr[0], addr[1], packet_type)
            return False

        # Receives the respond
        logging.debug("Wait for reply from server")
        try:
            resp_json, _ = client.recvfrom(self.__buffer_size)
        except OSError:
            logging.error(
                "Cannot receive reply! (addr = %s:%d, packet_type = \"%s\")",
                addr[0], addr[1], packet_type)
            return False

        try:
            resp_data = json.loads(resp_json.decode())
        except json.JSONDecodeError:
            logging.error(
                "Response is not JSON-encoded format! (addr = %s:%d, "
                "packet_type = \"%s\", resp_data = \"%s\")",
                addr[0], addr[1], packet_type, resp_json.decode())
            return False

        logging.debug("Finish sending packet")

        return resp_data

    def __server_listening_thread(self):
        """
        Thread which listens to incoming packet. The packet will be processed
        and replied by one of the registered packet handler functions
        depends on the packet type.
        """

        logging.debug("Start listening to incoming packet")

        while True:

            # Waits for incoming packet
            logging.debug("Wait for incoming packet")

            # try:
            data, address = self.__server.recvfrom(self.__buffer_size)
            # except OSError:
            #    continue

            threading.Thread(target=self.__handle_incoming_packet,
                             daemon=True,
                             args=(address, data,)).start()

        logging.debug("Finish listening to incoming packet")

    def __handle_incoming_packet(self, address, data):
        """
        Each incoming packet will be handled in a seperate thread to make
        sure that the server is always ready for incoming packets.
        """

        try:
            packet = json.loads(data.decode())

            packet_type = packet["type"]
            packet_data = packet["data"]
        except json.JSONDecodeError:
            logging.error("Packet is in wrong format! "
                          "(addr = %s:%d, data = \"%s\")",
                          address[0], address[1], data.decode())
            return

        logging.debug(
            "Received packet (address = %s:%d, packet_type = \"%s\"",
            address[0], address[1], packet_type)

        # Forwards the packet to corresponding module
        # Sends back the reply of the module
        logging.debug("Find and call packet handler")
        if packet_type in self.__handler_list:
            # Starts a new transaction and calls the packet handler
            tid = self.__transaction_manager.start()

            resp_data = self.__handler_list[packet_type](
                tid, address, packet_data)

            success = self.__transaction_manager.finish(tid)
            if not success:
                resp_data = False

            # Answers the client
            logging.debug("Answer the client")
            resp_json = json.dumps(resp_data)

            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client.settimeout(self.__timeout)
                client.sendto(resp_json.encode(), address)
            except OSError:
                logging.error("Cannot reply! (addr = %s:%d)",
                              address[0], address[1])
        else:
            logging.warning(
                "Unknown packet! (addr = %s:%d, packet_type = \"%s\")",
                address[0], address[1], packet_type)
