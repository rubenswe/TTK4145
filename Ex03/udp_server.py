import socket

PORT = 20012

def main():

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.bind(("", PORT))

    while True:
        data, addr = conn.recvfrom(1024)
        print("From %s: %s" % (addr, data))

        conn.sendto("The message '%s' has been received!" % (data), addr)

if __name__ == "__main__":
    main()
