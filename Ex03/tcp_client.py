import socket

HOST = "127.0.0.1"
PORT = 20012

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    while True:
        s.connect((HOST, PORT))
        s.sendall("Hello, world!")
        data = s.recv(1024)
        s.close()
        print("Received", repr(data))

if __name__ == "__main__":
    main()
