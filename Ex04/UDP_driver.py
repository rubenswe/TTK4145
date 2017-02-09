import socket
import json
from time import sleep

# Config:
####################################
# address = "localhost"
# PORT = 20058
# someTimeoutFunction (?)
####################################


class UdpServer(object):
    def __init__(self, PORT):
        self.port = PORT
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(PORT)  # Can you bind without having an address?
        self.connection_made = False  # When should this be set to True? / When is an connection made?

    def listen(self):
        while True:
            if self.connection_made:
                # Need to use threads here is case several connections are made at the same time?
                data, address = json.loads(self.server.recvfrom(1024))
                print("Received: {}\n From: {}".format(data, address))
                self.server.sendto("The data {} from {} has been received!".format(data, address))
            else:
                self.connection_made = False
                break
        # Correct place to close socket?
        self.server.close()
        print("Server stopped.")


class UdpClient(object):
    def __init__(self, address, PORT):
        self.address = (address, PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.AliveMsg = True
        self.data = []
        # self.client.sendto(data, self.address)  # Send the data/request ----> Should this be done in a function?

    def heartbeat(self):
        while True:
            self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            data = json.dumps(self.data)  # Encode data
            self.client.sendto(data, self.address)
            sleep(1)

    # If an request is made, call this function:
    # Should this be done in the init function?
    def send_request(self, request):
        # Should this be in an infinite loop?
        self.data = json.dumps(request)
        self.client.sendto(self.data, self.address)


# How to use classes:
server = UdpServer(20058)
client = UdpClient("localhost", 20058)
