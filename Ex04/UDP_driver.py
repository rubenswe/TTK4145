
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
        self.address = ""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.address, self.port))  # Should this be in listen()?
        print("Socket info: {}".format(self.server.getsockname()))  # Tuple
        self.connection_made = False  # When should this be set to True?/When is an connection made? Is this necessary?

    def listen(self):
        print("Server is listening...")
        while True:
                # Need to use threads here in case several connections are made at the same time?
                # data, address = json.loads(self.server.recvfrom(1024))  # Decode data, recvfrom() or recv()?
                data, address = self.server.recvfrom(1024)
                self.address = address
                print("Received: {}\nFrom: {}".format(data, self.address))
                print("Socket info: {}".format(self.server.getsockname()))
                self.server.sendto(data, self.address)

    def broadcast(self):
        print("Server is broadcasting...")
        while True:
            print("The server's address is: {}".format(self.server.getsockname()[0]))
            print("The server's port is: {}".format(self.server.getsockname()[1]))
            sleep(2)
        pass


class UdpClient(object):
    def __init__(self, address, PORT):
        self.address = (address, PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.AliveMsg = True
        self.data = []
        # json.dumps(self.data)  # TESTING
        # self.client.sendto(data, self.address)  # Send the data/request ----> Should this be done in a function?

    # heartbeat() is untested
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
        # data = json.dumps(request)  # Encode data
        #  json.dumps(self.address)  # Encode address
        self.data = request.encode()
        self.client.sendto(self.data, self.address)  # TypeError: a bytes-like object is required, not 'str' <--- Get this when I try to use json
        print("The data {} is sent to {}".format(self.data, self.address))
        print("Socket info: {}".format(self.client.getsockname()))  # This prints address '0.0.0.0' and a random port... -> Does it have anything to say?

# How to use classes:
# server = UdpServer(20058)
# client = UdpClient("localhost", 20058)
