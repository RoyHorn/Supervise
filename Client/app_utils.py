import socket, threading
from threading import Thread
from PIL import Image

class Client(Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host  # The server's hostname or IP address
        self.port = port  # The port used by the server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messages = [] # each place (command, data)
        self.messages_lock = threading.Lock()

    def send_receive_messages(self):
        for cmmd, data in self.messages:
            self.client_socket.send(f'{cmmd}{str(len(data)).zfill(8)}{data}'.encode())
            self.messages.remove((cmmd,data))
            self.receive_messages()
        
    def receive_messages(self):
        type = self.client_socket.recv(1).decode()
        cmmd = self.client_socket.recv(1).decode()
        length = int(self.client_socket.recv(8).decode())
        data = self.client_socket.recv(length)

        if type == 'r':
            self.handle_response(cmmd, data)
        elif type == 'u':
            self.update(cmmd)
        
    def request_data(self, cmmd, data=''):
        with self.messages_lock:
            self.messages.append((cmmd, data))

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

    def close_client(self):
        self.client_socket.close()

    def open(self):
        '''runs the client, connects to the server'''
        self.client_socket.connect((self.host, self.port))

        while True:
            self.send_receive_messages()

    def run(self):
        client_thread = threading.Thread(target= self.open)
        client_thread.run()

if __name__ == '__main__':
    a = Client('127.0.0.1', 8008)
    a.start()
    a.request_data(1)
    a.request_data(3)