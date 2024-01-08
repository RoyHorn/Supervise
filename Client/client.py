import socket
from PIL import Image


class Client():
    def __init__(self, host, port):
        self.host = host  # The server's hostname or IP address
        self.port = port  # The port used by the server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def show_screenshot(self, data):
        '''this function translates the photo from byte back to png and shows it'''
        image = Image.frombytes("RGB", (1920, 1080), data)
        image.show()

    def handle_response(self, cmmd, data):
        '''handels the server rsponses - for images opens the specific func, 
        for screentime shows the data in the specific window...'''
        if cmmd == '3': #3 - screenshot command
            self.show_screenshot(data)
        else:
            print("Received from server:", data.decode())

    def update(self, cmmd):
        '''handels changes made by other clients - 
        for example: another user started a block, this func will make sure that 
        this client updates to show that there is a block currently running'''
        if cmmd == '1': #1 - block command
            pass #should change blocking label
        if cmmd == '2': #2 - unblock command
            pass #should change blocking label

    def run(self):
        '''runs the client, connects to the server'''
        self.client_socket.connect((self.host, self.port))

        while True:
            message = input("Enter message to send (or 'quit' to exit): ")
            if message == 'quit':
                self.client_socket.send(b'100000004quit')
                self.client_socket.close()
                break

            self.client_socket.send(f'{message}{str(len(message)).zfill(8)}{message}'.encode())
            type = self.client_socket.recv(1).decode()
            cmmd = self.client_socket.recv(1).decode()
            length = int(self.client_socket.recv(8).decode())
            data = self.client_socket.recv(length)

            if type == 'r':
                self.handle_response(cmmd, data)
            elif type == 'u':
                self.update(cmmd)

a = Client('localhost', 5555)
a.run()