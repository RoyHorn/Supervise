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
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rlist = []
        self.wlist = []
        self.xlist = []
        self.encryption = Encryption()
        self.server_public_key = ''
        self.messages = []
        self.messages_lock = threading.Lock()
        self.blocked_sites = -1
        self.browsing_history = -1
        self.screentime_list = -1
        self.auth_needed = -1
        self.auth_succeded = -1
        self.screentime_limit = -1
        self.connection_succesful = -1
        self.block_button = None

        # Define resolvers
        self.authorization_resolver = {
            '0': self.auth_needed_handler,
            '1': self.auth_not_needed_handler,
            '2': self.auth_response_handler
        }
        
        self.response_resolver = {
            '3': self.screenshot_handler,
            '4': self.blocked_sites_handler,
            '7': self.screentime_list_handler,
            '8': self.screentime_limit_handler
        }
        
        self.update_resolver = {
            '1': self.block_handler,
            '2': self.unblock_handler
        }

    def send_receive_messages(self):
        self.rlist, self.wlist, self.xlist = select.select([self.client_socket], [self.client_socket], [])
        if self.client_socket in self.rlist:
            self.receive_messages()
        for type, cmmd, data in self.messages:
            cipher = self.format_message(type, cmmd, data)
            self.client_socket.send(str(len(cipher)).zfill(8).encode())
            self.client_socket.sendall(cipher)
            self.messages.remove((type, cmmd, data))
            self.receive_messages()
        
    def receive_messages(self):
        try:
            data_len = int(self.recvall(self.client_socket, 8).decode())
            ciphertext = self.recvall(self.client_socket, data_len)
        except:
            return

        type, cmmd, data = self.encryption.decrypt(ciphertext)

        if type == 'a':
            self.authorization_resolver.get(cmmd, self.default_handler)(data)
        elif type == 'r':
            self.response_resolver.get(cmmd, self.default_handler)(data)
        elif type == 'u':
            self.update_resolver.get(cmmd, self.default_handler)()

    def recvall(self, sock: socket.socket, size: int) -> bytes:
        received_chunks = []
        buf_size = 1024
        remaining = size
        while remaining > 0:
            received = sock.recv(min(remaining, buf_size))
            if not received:
                raise Exception('unexpected EOF')
            received_chunks.append(received)
            remaining -= len(received)
        return b''.join(received_chunks)

    def auth_needed_handler(self, data):
        self.auth_needed = 1

    def auth_not_needed_handler(self, data):
        self.auth_needed = 0

    def auth_response_handler(self, data):
        self.auth_succeded = 1 if data.decode() == 'T' else 0

    def screenshot_handler(self, data):
        self.show_screenshot(pickle.loads(data))

    def blocked_sites_handler(self, data):
        data = pickle.loads(data)
        if isinstance(data, list):
            self.blocked_sites = data
        else:
            self.browsing_history = data

    def screentime_list_handler(self, data):
        self.screentime_list = pickle.loads(data)

    def screentime_limit_handler(self, data):
        self.screentime_limit = data.decode()

    def block_handler(self):
        self.set_block_button_text('End Block')

    def unblock_handler(self):
        self.set_block_button_text('Start Block')

    def default_handler(self, data=None):
        pass

    def format_message(self, type, cmmd, data=''):
        msg = f'{type}{cmmd}{data}'.encode()
        ciphertext = self.encryption.encrypt(self.server_public_key, msg)
        return ciphertext

    def request_data(self, cmmd, data='', type='r'):
        with self.messages_lock:
            self.messages.append((type, cmmd, data))

    def show_screenshot(self, data):
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

    def run(self):
        try:
            self.client_socket.connect((self.host, self.port))
            self.connection_succesful = 1
        except:
            self.connection_succesful = 0
            return
        self.client_socket.send(self.encryption.get_public_key())
        self.server_public_key = self.encryption.recv_public_key(self.recvall(self.client_socket, 271))
        while True:
            self.send_receive_messages()

class Encryption():
    def __init__(self):
        self.key = RSA.generate(1024)
        self.public_key = self.key.publickey()
        self.private_key = self.key

    def encrypt(self, key, data) -> bytes:
        cipher = PKCS1_OAEP.new(key)
        chunk_size = 128 
        encrypted_data = b""
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_data += encrypted_chunk
        return encrypted_data
        
    def decrypt(self, ciphertext) -> tuple[str, str, bytes]:
        decrypt_cipher = PKCS1_OAEP.new(self.private_key)
        chunk_size = 128 
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
