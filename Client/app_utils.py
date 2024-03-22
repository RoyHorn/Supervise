import select
import socket
import threading
from PIL import Image
import pickle
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from threading import Thread
import gzip

class Client(Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host  # The server's hostname or IP address
        self.port = port  # The port used by the server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP client socket
        self.rlist = [] # select.select read list - list of the sockets who sent data
        self.wlist = [] # select.select write list - list of the sockets that can recv data
        self.xlist = [] # select.select error list - list of the sockets that has errors
        self.encryption = Encryption() 
        self.server_public_key = ''
        self.messages = [] # each place (command, data)
        self.messages_lock = threading.Lock()
        self.blocked_sites = -1 # list of blocked sites, will be recived from server
        self.browsing_history = -1 # dictionary contains browsing history, will be recived from server
        self.screentime_list = -1 # each place (date, screentime)
        self.auth_needed = -1 
        self.auth_succeded = -1
        self.screentime_limit = -1
        self.block_button = ''


    def send_receive_messages(self):
        """ Sends pending messages to the server and receives messages from the server.
        This handles the client-server communication.
        """
        #responsible for update messages
        self.rlist, self.wlist, self.xlist = select.select([self.client_socket], [self.client_socket], [])
        if self.client_socket in self.rlist:
            self.receive_messages()

        #responsible for responses
        for type, cmmd, data in self.messages:
            cipher = self.format_message(type, cmmd, data)
            self.client_socket.send(str(len(cipher)).zfill(8).encode())
            self.client_socket.sendall(cipher)
            self.messages.remove((type, cmmd, data))
            self.receive_messages()
        
    def receive_messages(self):
        """ Receive messages from the server and handle them appropriately.
        
        This method checks for any incoming data from the server and processes it.
        It will receive things like the blocked sites list, browsing history etc.
        and store them in the appropriate instance variables.
        """
        data_len = int(self.client_socket.recv(8).decode())
        ciphertext = self.client_socket.recv(data_len)
        #TODO: add recv all function

        type, cmmd, data = self.encryption.decrypt(ciphertext)

        if type == 'a':
            self.handle_authorization(cmmd, data)
        elif type == 'r':
            self.handle_response(cmmd, data)
        elif type == 'u':
            self.update(cmmd)

    def handle_authorization(self, cmmd, data):
        """Handles authorization commands and data sent from the server.

        This method will process any authorization-related messages from 
        the server and update state accordingly.
        """

        if cmmd == '0':
            self.auth_needed = 1
        elif cmmd == '1':
            self.auth_needed = 0
        elif cmmd == '2':
            if data.decode() == 'T':
                self.auth_succeded = 1
            else: 
                self.auth_succeded = 0
    

    def handle_response(self, cmmd, data):
        """Handles response commands and data sent from the server."""

        if cmmd == '3': #3 - screenshot command
            self.show_screenshot(pickle.loads(data))
        elif cmmd == '4':
            data = pickle.loads(data)
            if isinstance(data, list):
                self.blocked_sites = data
            else:
                self.browsing_history = data
        elif cmmd == '7':
            self.screentime_list = pickle.loads(data)
        elif cmmd == '8':
            self.screentime_limit = data.decode()

    def update(self, cmmd):
        """
        Updates the block button text based on commands from the server.
    
        This method handles any update commands regarding the block state sent from the server,
        and updates the client's block button text accordingly.
        """

        if cmmd == '1': #1 - block command
            self.set_block_button_text('End Block')
        if cmmd == '2': #2 - unblock command
            self.set_block_button_text('Start Block')

    def format_message(self, type, cmmd, data=''):
        """Formats a message to send to the server.
        
        This encryptes message to send to the server.
        
        Args:
        type: The type of message (e.g. 'r' for response).
        cmmd: The command to send.
        data: Optional data to include with the message.
        
        Returns:
        The encrypted message string.
        """
        msg = f'{type}{cmmd}{data}'.encode()

        ciphertext = self.encryption.encrypt(self.server_public_key, msg)

        return ciphertext

    def request_data(self, cmmd, data='', type='r'):
        """
        Appends messages to the messages list.
        
        Args:
        cmmd: The command to send. 
        data: Optional data to include.
        type: The type of request (default 'r' for response).
        """

        with self.messages_lock:
            self.messages.append((type, cmmd, data))

    def show_screenshot(self, data):
        """
        Shows a screenshot image.
        
        Decompresses image data received from the server and displays
        the screenshot image.
        """

        decompressed_data = gzip.decompress(data)
        image = Image.frombytes("RGB", (1920, 1080), decompressed_data)
        image.show()

    def get_blocked_sites_list(self):
        return self.blocked_sites
    
    def get_screentime_list(self):
        return self.screentime_list
    
    def get_screentime_limit(self):
        return self.screentime_limit
    
    def set_block_button(self, block_button):
        self.block_button = block_button

    def set_block_button_text(self, data):
        self.block_button.config(text=data)

    def close_client(self):
        cipher = self.format_message('r', 0)
        self.client_socket.send(str(len(cipher)).zfill(8).encode())
        self.client_socket.sendall(cipher)
        self.client_socket.close()

    def open(self):
        """
        Opens the client socket connection.
        """

        self.client_socket.connect((self.host, self.port))
        self.client_socket.send(self.encryption.get_public_key())
        self.server_public_key = self.encryption.recv_public_key(self.client_socket.recv(271))

        while True:
            self.send_receive_messages()

    def run(self):
        '''the thread start method'''
        client_thread = threading.Thread(target=self.open)
        client_thread.start()

class Encryption():
    def __init__(self):
        self.key = RSA.generate(1024)
        self.public_key = self.key.publickey()
        self.private_key = self.key

    def encrypt(self, key, data):
        """
        Encrypts the given data with the provided key.
        
        Args:
            key: The encryption key to use.
            data: The data to encrypt.
            
        Returns:
            The encrypted data.
        """
        cipher = PKCS1_OAEP.new(key)
        chunk_size = 128  # Adjust this value based on your key size
        encrypted_data = b""

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_data += encrypted_chunk

        return encrypted_data
        
    def decrypt(self, ciphertext):
        """
        Decrypts the given ciphertext using the private key.
        
        Args:
            ciphertext: The ciphertext to decrypt.
        
        Returns:
            The decrypted plaintext.
        """
        decrypt_cipher = PKCS1_OAEP.new(self.private_key)
        chunk_size = 128  # Adjust this value based on your key size
        decrypted_message = b""

        for i in range(0, len(ciphertext), chunk_size):
            chunk = ciphertext[i:i + chunk_size]
            decrypted_chunk = decrypt_cipher.decrypt(chunk)
            decrypted_message += decrypted_chunk

        type = decrypted_message[:1].decode()
        cmmd = decrypted_message[1:2].decode()
        data = decrypted_message[2:]

        return type, cmmd, data
    
    def get_public_key(self):
        return self.public_key.export_key()
    
    def recv_public_key(self, pem_key):
        return RSA.import_key(pem_key)
