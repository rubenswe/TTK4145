import socket

HOST = "127.0.0.1"
PORT = 20012

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))

    print(HOST, PORT)
    s.listen(1)
    conn, addr = s.accept()
    print("Connected by ", addr)

    while True:
        try:
            data = conn.recv(1024)

            if not data: break

            print("Client says: "+data)
            conn. sendall("Server says: Hi!")

        except socket.error:
            print("Error occurred.")
            break
    conn.close()

if __name__ == "__main__":
    main()
