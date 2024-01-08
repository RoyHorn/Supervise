import socket
from threading import Thread
from server_utils import ActiveTime, Screenshot, Block

class Server(Thread):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.BUFF_SIZE = 1028
        self.block = Block()

    def operate(self, cmmd, client_socket):
        if cmmd == 'block':
            client_socket.send('00000007blocked'.encode())
            self.block.start()
        elif cmmd == 'screenshot':
            image = Screenshot().screenshot()
            client_socket.send((str(len(image)).zfill(8)).encode())
            client_socket.sendall(image)
        else:
            client_socket.send(b'00000004test')


    def serve(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")
        
        active_time = ActiveTime().start()

        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Connected by {address}")

            length = int(client_socket.recv(8).decode())
            data = client_socket.recv(length).decode()

            self.operate(data, client_socket)

    # def send(self, client_socket, data):
    #     while len(data) > 0:
    #         client_socket.send(data[:self.BUFF_SIZE])
    #         data = data[self.BUFF_SIZE:]

a = Server('0.0.0.0', 2017)
a.serve()