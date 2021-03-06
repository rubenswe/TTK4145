import socket

HOST = "127.0.0.1"
PORT = 20012


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    while True:
        print("Sending...")
        msg = input("Message: ")
        s.sendall(msg.encode("utf-8"))
        print("Receiving...")
        data = s.recv(1024)
        print("Received", repr(data))

    s.close()

if __name__ == "__main__":
    main()
