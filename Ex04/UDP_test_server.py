from UDP_driver import UdpServer, UdpClient
import json

PORT = 20058
server = UdpServer(PORT)
server.listen()
