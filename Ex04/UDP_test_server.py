from UDP_driver import UdpServer, UdpClient
import json

IP = "localhost"  # Should IP be fixed?
PORT = 20012
server = UdpServer(PORT)
server.listen()
