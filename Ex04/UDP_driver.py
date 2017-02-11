
import socket
import json
from time import sleep

# Config:
####################################
# address = "localhost"
# PORT = 20058
# someTimeoutFunction (?) --> If a client doesnt respond in som time, declare it dead(Should this be a class function?)
####################################


class UdpServer(object):
    def __init__(self, PORT):
        self.port = PORT
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(("", PORT))
        self.connection_made = False  # When should this be set to True?/When is an connection made? Is this necessary?

    def listen(self):
        print("Server is listening...")
        while True:
                # Need to use threads here in case several connections are made at the same time?
                data, address = json.loads(self.server.recv(1024))  # Decode data, recvfrom() or recv()?
                print("Received: {}\n From: {}".format(data, address))
                self.server.sendto("The data {} from {} has been received!".format(data, address))
        # Correct place to close socket?
        # self.server.close()
        # print("Server stopped.")


class UdpClient(object):
    def __init__(self, address, PORT):
        self.address = (address, PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.AliveMsg = True
        self.data = []
        # json.dumps(self.data)  # TESTING
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
    # Should the request be taken in as an argument?
    def send_request(self, request):
        # Should this be in an infinite loop? Or only called when an request is made?
        print(request)  # TESTING
        self.data = json.dumps(request)  # Encode data
        print(self.data)  # TESTING
        self.client.sendto(self.data, self.address)  # ERROR: expected self.data to be an byte-like object, not 'str'.


# How to use classes:
# server = UdpServer(20058)
# client = UdpClient("localhost", 20058)
