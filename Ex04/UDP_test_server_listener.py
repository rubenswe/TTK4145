from UDP_driver import UdpServer, UdpClient

PORT = 20012
ADDRESS = ""
server = UdpServer(ADDRESS, PORT)  # self.serving_address = ADDRESS
server.listen()
