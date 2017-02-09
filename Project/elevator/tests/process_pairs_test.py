"""
Created on Feb 9, 2017

@author: Viet-Hoa Do
"""

import process_pairs
import time
import threading
import logging


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

    def __init__(self):
        self.__running = False
        self.__handler_list = dict()
        self.__partner = None

    def set_partner(self, partner):
        self.__partner = partner

    def start_server(self):
        self.__running = True

    def stop_server(self):
        self.__running = False

    def add_packet_handler(self, packet_type, handler_func):
        self.__handler_list[packet_type] = handler_func

    def send_packet(self, destination_addr, packet_type, data):
        return self.__partner.on_receive(packet_type, data)

    def on_receive(self, packet_type, data):
        if self.__running and packet_type in self.__handler_list:
            return self.__handler_list[packet_type](None, data)
        return False


class ProcessPairsConfig(object):

    def __init__(self):
        self.partner_ip_address = ""
        self.partner_port = 0
        self.max_attempts = 2


class Config(object):

    def __init__(self):
        self.process_pairs = ProcessPairsConfig()


def main():
    logging.basicConfig(level=logging.DEBUG)

    # System 1
    config_1 = Config()
    counter_1 = Counter("COUNTER 1")
    network_1 = Network()

    # System 2
    config_2 = Config()
    counter_2 = Counter("COUNTER 2")
    network_2 = Network()

    # Connects 2 systems
    network_1.set_partner(network_2)
    network_2.set_partner(network_1)

    # Activates primary/backup switching
    switcher_1 = process_pairs.PrimaryBackupSwitcher()
    switcher_2 = process_pairs.PrimaryBackupSwitcher()

    switcher_1.init(config_1, {"counter": counter_1}, network_1)

    time.sleep(5)
    switcher_2.init(config_2, {"counter": counter_2}, network_2)

    # Kills system 1
    time.sleep(20)
    switcher_1.set_primary_mode(False)
    time.sleep(20)

if __name__ == "__main__":
    main()
