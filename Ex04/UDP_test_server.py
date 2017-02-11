from UDP_driver import UdpServer, UdpClient
import json

IP = "localhost"
PORT = 20012
server = UdpServer(PORT)
server.listen()
# server.broadcast()
