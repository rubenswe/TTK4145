import logging
import core
import network
import transaction


logging.basicConfig(format="%(levelname)8s | %(asctime)s : %(message)s"
                    " (%(module)s.%(funcName)s)",
                    level=logging.INFO)


received_data = None


def on_receive_echo(tid, addr, data):
    """
    Called when the network module has received an echo packet.
    Returns the received data back to the sender.
    """

    global received_data

    logging.debug("From %s:%d: %s", addr[0], addr[1], data)
    received_data = data

    return data


def main():
    """
    Starts
    """

    config_0 = core.Configuration("../config/local-test.conf", "floor_0")
    config_1 = core.Configuration("../config/local-test.conf", "floor_1")

    transaction_manager_0 = transaction.TransactionManager()
    transaction_manager_1 = transaction.TransactionManager()

    network_0 = network.Network()
    network_1 = network.Network()

    network_0.init(config_0, transaction_manager_0)
    network_1.init(config_1, transaction_manager_1)

    network_1.add_packet_handler("echo", on_receive_echo)

    tid_0 = transaction_manager_0.start()
    network_0.start(tid_0)
    transaction_manager_0.finish(tid_0)

    tid_1 = transaction_manager_1.start()
    network_1.start(tid_1)
    transaction_manager_1.finish(tid_1)

    # Sends echo packet from 0 to 1, expects 1 receives the right message
    # and replies the same one
    msg = "Haha"
    resp = network_0.send_packet(network_1.__dict__["_Network__address"],
                                 "echo", msg)
    if resp == msg and received_data == msg:
        print("PASS 1")
    else:
        print("FAIL 1")

    # Sends echo packet from 1 to 0, expects no reply
    resp = network_1.send_packet(network_0.__dict__["_Network__address"],
                                 "echo", msg)
    if resp is False:
        print("PASS 2")
    else:
        print("FAIL 2")

if __name__ == "__main__":
    main()
