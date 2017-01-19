import socket

HOST = "127.0.0.1"
PORT = 20012

def main():
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        msg = raw_input("Message: ")
        conn.sendto(msg, (HOST, PORT))

if __name__ == "__main__":
    main()
