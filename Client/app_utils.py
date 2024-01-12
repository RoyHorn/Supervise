import socket, threading
from threading import Thread
from PIL import Image
from icecream import ic
import pickle

class Client(Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host  # The server's hostname or IP address
        self.port = port  # The port used by the server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messages = [] # each place (command, data)
        self.messages_lock = threading.Lock()
        self.sites_list = []
        self.screentime_list = []

    def send_receive_messages(self):
        '''responsible to first send requests to the server then receive the results and show to correct behaviour'''
        for cmmd, data in self.messages:
            #TODO add encryption
            self.client_socket.send(f'{cmmd}{str(len(data)).zfill(8)}{data}'.encode())
            self.messages.remove((cmmd,data))
            self.receive_messages()
        
    def receive_messages(self):
        '''recives the response from the server in chunks then moves to the correct place according to type(response or update)'''
        #TODO add decryption
        type = self.client_socket.recv(1).decode()
        cmmd = self.client_socket.recv(1).decode()
        length = int(self.client_socket.recv(8).decode())
        data = self.client_socket.recv(length)

        if type == 'r':
            self.handle_response(cmmd, data)
        elif type == 'u':
            self.update(cmmd)
        
    def request_data(self, cmmd, data=''):
        '''allows to gui to add messages to be sent, uses the threading lock in order to stop the thread to be able to insert to the messages list'''
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
        elif cmmd == '4':
            self.sites_list = pickle.loads(data)
        elif cmmd == '7':
            self.screentime_list = pickle.loads(data)
        else:
            pass

    def get_sites_list(self):
        '''returns to the gui the formmated list of blocked sites'''
        return self.sites_list
    
    def get_screentime_list(self):
        return self.screentime_list

    def update(self, cmmd):
        '''handels changes made by other clients - 
        for example: another user started a block, this func will make sure that 
        this client updates to show that there is a block currently running'''
        if cmmd == '1': #1 - block command
            pass #should change blocking label
        if cmmd == '2': #2 - unblock command
            pass #should change blocking label

    def close_client(self):
        self.client_socket.send(b'900000000')
        self.client_socket.close()

    def open(self):
        '''runs the client, connects to the server'''
        self.client_socket.connect((self.host, self.port))

        while True:
            self.send_receive_messages()

    def run(self):
        '''the thread start method'''
        client_thread = threading.Thread(target= self.open)
        client_thread.run()