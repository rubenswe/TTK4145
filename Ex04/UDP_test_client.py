from UDP_driver import UdpServer, UdpClient
from time import sleep
import json

PORT = 20058
client = UdpClient("localhost", PORT)
request = "This is an request..."
for i in range(0, 5):
    client.send_request(request)
    sleep(2)