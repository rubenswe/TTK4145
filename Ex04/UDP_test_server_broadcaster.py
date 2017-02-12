from UDP_driver import UdpServer, UdpClient

broadcast_address = ""  # Broadcast address of computer, found by 'ifconfig' in terminal
address = ""  # Internet address of computer, found by doing 'ifconfig' in terminal
PORT = 20012
server = UdpServer(adress, PORT)  # self.serving_address = ADDRESS
server.address = broadcast_address
server.broadcast()
