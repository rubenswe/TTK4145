"""
Created on Feb 9, 2017

@author: Viet-Hoa Do
"""

import process_pairs
import time
import threading
import logging
import socket
import json
import argparse
import sys


class Counter(process_pairs.PrimaryBackupSwitchable):

    def __init__(self, name):
        self.__lock_state = threading.Lock()

        self.__name = name
        self.__counter = 0
        self.__running = True

    def start(self):
        print("[%s] Start counting from %d" % (self.__name, self.__counter))

        thread = threading.Thread(target=self.__do_count, daemon=True)
        self.__running = True
        thread.start()

    def __do_count(self):
        while self.__running:
            self.__lock_state.acquire()
            self.__counter += 1
            print("[%s] Counter = %d" % (self.__name, self.__counter))
            self.__lock_state.release()

            time.sleep(1)

    def stop(self):
        print("STOPPPPPPPPPPPPPPPPP %s" % (self.__name))
        self.__running = False

    def export_state(self):
        self.__lock_state.acquire()
        state = {"counter": self.__counter}
        self.__lock_state.release()

        return state

    def import_state(self, state):
        self.__lock_state.acquire()
        self.__counter = state["counter"]
        self.__lock_state.release()


class Network(object):

    def __init__(self, config):
        self.__config = config

        self.__running = False
        self.__handler_list = dict()

        self.__server = None

    def start_server(self, address):
        if self.__running:
            self.stop_server()

        logging.debug("Start server %s:%d" % address)

        self.__running = True

        self.__server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            try:
                self.__server.bind(address)
                break
            except OSError:
                pass

        listening = threading.Thread(target=self.server_listening, daemon=True)
        listening.start()

    def stop_server(self):
        if not self.__running:
            return

        self.__running = False

        self.__server.close()
        self.__server = None

    def add_packet_handler(self, packet_type, handler_func):
        self.__handler_list[packet_type] = handler_func

    def send_packet(self, destination_addr, packet_type, data):

        # Prepares the data to sent
        packet = {"type": packet_type, "data": data}
        packet_json = json.dumps(packet)

        # Sends the packet
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(self.__config.timeout)

        try:
            client.sendto(packet_json.encode(), destination_addr)
        except socket.timeout:
            return False

        # Receives the respond
        try:
            resp_json, _ = client.recvfrom(1024)
        except socket.timeout:
            return False

        resp_data = json.loads(resp_json.decode())

        return resp_data

    def server_listening(self):

        while self.__running:
            data, address = self.__server.recvfrom(1024)
            packet = json.loads(data.decode())

            packet_type = packet["type"]
            packet_data = packet["data"]

            if packet_type in self.__handler_list:
                resp_data = self.__handler_list[packet_type](
                    address, packet_data)

                resp_json = json.dumps(resp_data)
                self.__server.sendto(resp_json.encode(), address)


class NetworkConfig(object):

    def __init__(self):
        self.ip_address = "localhost"
        self.port = 12345
        self.timeout = 0.5


class ProcessPairsConfig(object):

    def __init__(self):
        self.partner_ip_address = "localhost"
        self.partner_port = 12346
        self.max_attempts = 2

        self.period = 0.5
        self.timeout = 1.5


class Config(object):

    def __init__(self):
        self.network = NetworkConfig()
        self.process_pairs = ProcessPairsConfig()


def server_on_receive(address, data):
    print("[Received] %s:%d : %s" % (address[0], address[1], data))
    return data


def main():
    logging.basicConfig(level=logging.DEBUG)

    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="primary")
    args = parser.parse_args()
    print("Arguments: ", args)

    primary = True
    if args.mode == "backup":
        primary = False

    # Initializes
    config = Config()
    network = Network(config.network)
    counter = Counter("Counter")

    module_list = {"counter": counter}
    pp = process_pairs.ProcessPair()
    pp.init(config, module_list, network, primary)

    while True:
        continue

    """switcher = PrimaryBackupSwitcher()
    switcher.init(config, module_list, network)

    while True:
        continue"""

    """if False:
        network.add_packet_handler("ping", server_on_receive)
        network.start_server()

        while True:
            continue
    else:
        while True:
            message = input("Message: ")
            resp = network.send_packet(("localhost", 12345), "ping", message)
            print("Response: %s" % resp)"""

if __name__ == "__main__":
    main()
