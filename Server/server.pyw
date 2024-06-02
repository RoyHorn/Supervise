import datetime
import pickle
import select
import socket
import threading
import time
import logging
from functools import partial
from utils.active_time import ActiveTime
from utils.block import Block
from utils.database import Database
from utils.encryption import Encryption
from utils.screenshot import Screenshot
from utils.two_factor_authentication import TwoFactorAuthentication
from utils.web_blocker import WebBlocker

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Server:
    def __init__(self, host, port, results):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.encryption = Encryption()
        self.block = Block()
        self.web_blocker = WebBlocker()
        self.database = Database()
        self.database.create_time_limit_table()
        self.two_factor_auth = TwoFactorAuthentication()
        self.active_time = ActiveTime()
        self.active_time.start()
        self.time_limit = self.database.get_time_limit()
        self.client_sockets = []
        self.socket_to_publickey = {}
        self.messages = []
        self.rlist = []
        self.wlist = []
        self.xlist = []
        self.results = {key: partial(func, self) for key, func in results.items()}

    def send_messages(self):
        for type, cmmd, msg, receivers in self.messages:
            for receiver in receivers:
                if receiver in self.wlist:
                    cipher = self.format_message(type, cmmd, msg, receiver)
                    receiver.send(str(len(cipher)).zfill(8).encode())
                    receiver.sendall(cipher)
                    receivers.remove(receiver)
            if not receivers:
                self.messages.remove((type, cmmd, msg, receivers))

    def handle_commands(self, cmmd: str, msg: str, client: socket.socket):
        resolver = self.results.get(cmmd, self.default_response)
        resolver(msg, client)

    def start_computer_block(self, msg, client):
        logging.info(f"Start computer block: client={client.getpeername()}")
        self.messages.append(('u', 1, '', self.client_sockets.copy()))
        self.block.start()

    def end_computer_block(self, msg, client):
        logging.info(f"End computer block: client={client.getpeername()}")
        self.messages.append(('u', 2, '', self.client_sockets.copy()))
        self.block.end_block()
        self.block = Block()

    def take_screenshot(self, msg, client):
        logging.info(f"Screenshot request: client={client.getpeername()}")
        image = Screenshot().screenshot()  # Assuming Screenshot is a defined class
        self.messages.append(('r', 3, image, [client]))

    def request_web_blocker_data(self, msg, client):
        logging.info(f"Blocked sites request: client={client.getpeername()}")
        web_list = pickle.dumps(self.web_blocker.get_sites())
        browsing_history = pickle.dumps(self.web_blocker.build_history_string())
        self.messages.append(('r', 4, web_list, [client]))
        self.messages.append(('r', 4, browsing_history, [client]))

    def add_website_to_blocker(self, msg, client):
        logging.info(f"Add website to blocker: domain={msg}, client={client.getpeername()}")
        self.messages.append(('r', 5, msg, [client]))
        self.web_blocker.add_website(msg)

    def remove_website_from_blocker(self, msg, client):
        logging.info(f"Remove website from blocker: domain={msg}, client={client.getpeername()}")
        self.messages.append(('r', 6, msg, [client]))
        self.web_blocker.remove_website(msg)

    def request_screentime_data(self, msg, client):
        logging.info(f"Screentime data request: client={client.getpeername()}")
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        time_active = self.active_time.get_active_time()
        self.database.log_screentime(today_date, time_active)
        screentime_data = pickle.dumps(self.database.get_last_week_data())
        self.messages.append(('r', 7, screentime_data, [client]))

    def request_screentime_limit(self, msg, client):
        logging.info(f"Screentime limit request: limit={self.time_limit}, client={client.getpeername()}")
        self.messages.append(('r', 8, self.time_limit, [client]))

    def update_screentime_limit(self, msg, client):
        logging.info(f"Update screentime limit: new_limit={msg}, client={client.getpeername()}")
        self.database.change_time_limit(msg)
        self.time_limit = msg
        self.messages.append(('r', 9, self.time_limit, [client]))

    def quit_client(self, msg, client):
        logging.info(f"Client disconnected {client.getpeername()}")
        client.close()
        self.two_factor_auth.stop_code_display()
        self.client_sockets.remove(client)

    def default_response(self, msg, client):
        logging.info(f"Default response: msg={msg}")
        self.messages.append(('r', 'default', msg, self.client_sockets.copy()))

    def handle_authorization(self, code: str, client: socket.socket):
        if self.two_factor_auth.verify_code(int(code)):
            self.messages.append(('a', 2, 'T', [client]))
            client_ip, _ = client.getpeername()
            self.database.insert_user(client_ip)
        else:
            self.messages.append(('a', 2, 'F', [client]))
            self.client_sockets.remove(client)
        self.two_factor_auth.stop_code_display()

    def update_handler(self):
        while True:
            time_now = datetime.datetime.now().time()
            if time_now.minute % 1 == 0:
                self.active_time.log_active_time()
                self.web_blocker.update_file()
            if not self.database.is_last_log_today():
                self.active_time.reset_active_time()
                self.messages.append(('u', 2, '', self.client_sockets.copy()))
            if self.active_time.get_active_time() >= float(self.time_limit):
                self.messages.append(('u', 1, '', self.client_sockets.copy()))
                self.block.start()
            time.sleep(60)

    def format_message(self, type: str, cmmd: str, data: str, client: socket.socket) -> bytes:
        if cmmd not in (3, 4, 7):
            data = str(data).encode()
        msg = f'{type}{cmmd}'.encode() + data
        ciphertext = self.encryption.encrypt(self.socket_to_publickey[client], msg)
        return ciphertext

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

    def start(self):
        threading.Thread(target=self.update_handler).start()
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        logging.info(f'Server started on {self.host}:{self.port}')
        while True:
            self.rlist, self.wlist, self.xlist = select.select([self.server_socket] + self.client_sockets, self.client_sockets, [])
            for client in self.rlist:
                if client is self.server_socket:
                    connection, (ip, port) = self.server_socket.accept()
                    self.client_sockets.append(connection)
                    logging.info(f'New user connected {(ip, port)}')
                    self.socket_to_publickey[connection] = self.encryption.recv_public_key(self.recvall(connection, 271))
                    connection.send(self.encryption.get_public_key())
                    if not self.database.check_user(ip):
                        self.messages.append(('a', 0, '', [connection]))
                        self.two_factor_auth.display_code()
                    else:
                        self.messages.append(('a', 1, '', [connection]))
                    if self.block.get_block_state():
                        self.messages.append(('u', 1, '', [client]))
                    else:
                        self.messages.append(('u', 2, '', [client]))
                elif client in self.client_sockets:
                    if client in self.rlist:
                        try:
                            data_len = int(self.recvall(client, 8).decode())
                            ciphertext = self.recvall(client, data_len)
                        except:
                            logging.error('Error receiving data from client')
                            return
                        type, cmmd, msg = self.encryption.decrypt(ciphertext)
                        if msg == 'quit':
                            self.client_sockets.remove(client)
                            client.close()
                            break
                        if type == 'a':
                            self.handle_authorization(msg, client)
                        elif type == 'r':
                            self.handle_commands(cmmd, msg, client)
            self.send_messages()

    def stop(self):
        self.server_socket.close()
        logging.info('Server stopped')

def main():
    results = {
        '1': Server.start_computer_block,
        '2': Server.end_computer_block,
        '3': Server.take_screenshot,
        '4': Server.request_web_blocker_data,
        '5': Server.add_website_to_blocker,
        '6': Server.remove_website_from_blocker,
        '7': Server.request_screentime_data,
        '8': Server.request_screentime_limit,
        '9': Server.update_screentime_limit,
        '0': Server.quit_client
    }

    while True:
        try:
            a = Server('0.0.0.0', 8008, results)
            a.start()
        except Exception as e:
            logging.error(f'Server stopped with error: {e}')
            a.stop()

if __name__ == '__main__':
    main()