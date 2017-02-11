from UDP_driver import UdpServer, UdpClient

PORT = 20058
server = UdpServer(PORT)
server.listen()
