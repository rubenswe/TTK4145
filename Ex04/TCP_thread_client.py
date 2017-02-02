import socket
import threading
import socketserver


class Client:
    def connect(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def send(self, message):
        self.sock.sendall(message.encode("utf-8"))

    def receive(self):
        return self.sock.recv(1024)


if __name__ == "__main__":
    client = Client()
    client.connect('127.0.0.1', 20002)
    while True:
        message = input("Enter message: ")
        client.send(message)
        response = client.receive()
        print("Received: {}".format(response))