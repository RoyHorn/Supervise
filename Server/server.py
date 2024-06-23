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
        """
        Sends messages to the appropriate clients.
        
        This method is responsible for iterating through the `self.messages` list, which contains tuples of (message_type, command, message, receiver_list).
        For each tuple, it checks if the receiver is in the `self.wlist` (the list of sockets ready for writing), and if so, it formats the message using `self.format_message()` and sends it to the receiver.
        Once the message is sent, the receiver is removed from the `receivers` list.
        If the `receivers` list becomes empty, the entire tuple is removed from `self.messages`.
        """
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
        logging.info(f"%s started block" ,client.getpeername())
        self.messages.append(('u', 1, '', self.client_sockets.copy()))
        self.block.start()

    def end_computer_block(self, msg, client):
        logging.info(f"%s ended block" ,client.getpeername())
        self.messages.append(('u', 2, '', self.client_sockets.copy()))
        self.block.end_block()
        self.block = Block()

    def take_screenshot(self, msg, client):
        logging.info(f"%s requested screenshot" ,client.getpeername())
        image = Screenshot().screenshot()  # Assuming Screenshot is a defined class
        self.messages.append(('r', 3, image, [client]))

    def request_web_blocker_data(self, msg, client):
        logging.info("%s requested blocked sites list", client.getpeername())
        web_list = pickle.dumps(self.web_blocker.get_sites())
        browsing_history = pickle.dumps(self.web_blocker.build_history_string())
        self.messages.append(('r', 4, web_list, [client]))
        self.messages.append(('r', 4, browsing_history, [client]))

    def add_website_to_blocker(self, msg, client):
        logging.info("%s added website to blocker (domain = %s)", client.getpeername(), msg)
        self.messages.append(('r', 5, msg, [client]))
        self.web_blocker.add_website(msg)

    def remove_website_from_blocker(self, msg, client):
        logging.info("%s removed website from blocker (domain = %s)", client.getpeername(), msg)

        self.messages.append(('r', 6, msg, [client]))
        self.web_blocker.remove_website(msg)

    def request_screentime_data(self, msg, client):
        logging.info("%s requested screentime data", client.getpeername())
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        time_active = self.active_time.get_active_time()
        self.database.log_screentime(today_date, time_active)
        screentime_data = pickle.dumps(self.database.get_last_week_data())
        self.messages.append(('r', 7, screentime_data, [client]))

    def request_screentime_limit(self, msg, client):
        logging.info("%s requested screentime limit", client.getpeername())
        self.messages.append(('r', 8, self.time_limit, [client]))

    def update_screentime_limit(self, msg, client):
        logging.info("%s updated screentime limit (new_limit = %s)", client.getpeername(), msg)
        self.database.change_time_limit(msg)
        self.time_limit = msg

        if float(self.time_limit) >= self.active_time.get_active_time():
            self.end_computer_block('', client)

        self.messages.append(('r', 9, self.time_limit, [client]))

    def quit_client(self, msg, client):
        logging.info(f"%s disconnected", client.getpeername())
        client.close()
        self.two_factor_auth.stop_code_display()
        self.client_sockets.remove(client)

    def default_response(self, msg, client):
        logging.info(f"%s default message" ,client.getpeername())
        self.messages.append(('r', 'default', msg, self.client_sockets.copy()))

    def handle_authorization(self, code: str, client: socket.socket):
        """
        Handles the two-factor authentication process for a client connection.
        
        This method is responsible for verifying the code entered by the client and either allowing or rejecting the connection based on the code's validity.
        It updates the `self.messages` list with the necessary information to be sent to the client.
        
        Args:
            code (str): The code entered by the client.
            client (socket.socket): The client socket that sent the code.
        """

        if self.two_factor_auth.verify_code(int(code)):
            self.messages.append(('a', 2, 'T', [client]))
            client_ip, _ = client.getpeername()
            self.database.insert_user(client_ip)
        else:
            print('y')
            self.messages.append(('a', 2, 'F', [client]))
            self.client_sockets.remove(client)
        self.two_factor_auth.stop_code_display()

    def update_handler(self):
        """
        Updates the server's state at regular intervals, including:
        - Logging the active time for each client
        - Updating the web blocker file
        - Resetting the active time if a day had passed
        - Checking if the active time has exceeded the time limit and starting the block if so
        """
        while True:
            time_now = datetime.datetime.now().time()
            if time_now.minute % 1 == 0:
                self.active_time.log_active_time()
                self.web_blocker.update_file()

            if not self.database.is_last_log_today():
                self.active_time.reset_active_time()
                self.messages.append(('u', 2, '', self.client_sockets.copy()))
                logging.info(f"Server ended block - a day had passed")

            if self.active_time.get_active_time() >= float(self.time_limit):
                self.messages.append(('u', 1, '', self.client_sockets.copy()))
                if not self.block.block_state:
                    logging.info(f"Server started block - time limit exceeded")
                    self.block.start()

            time.sleep(60)

    def format_message(self, type: str, cmmd: str, data: str, client: socket.socket) -> bytes:
        """
        Formats a message to be sent to a client by encrypting the message using the client's public key.
        
        Args:
            type (str): The type of the message (e.g. 'r' for response).
            cmmd (int): The command code for the message.
            data (str): The data to be sent in the message.
            client (socket.socket): The client socket to which the message will be sent.
        
        Returns:
            ciphertext (bytes): The encrypted message.
        """

        if cmmd not in (3, 4, 7):
            data = str(data).encode()
        msg = f'{type}{cmmd}'.encode() + data
        ciphertext = self.encryption.encrypt(self.socket_to_publickey[client], msg)
        return ciphertext

    def recvall(self, sock: socket.socket, size: int) -> bytes:
        """
        Receives the full contents of a socket up to the specified size.
        
        Args:
            sock (socket.socket): The socket to receive data from.
            size (int): The total number of bytes to receive.
        
        Returns:
            bytes: The received data.
        
        Raises:
            Exception: If not the full data was received.
        """

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
        """
        Starts the server and handles the main server loop, including:
        - Accepting new client connections
        - Receiving and handling messages from connected clients
        - Updating the server state at regular intervals
        - Sending messages to clients as needed
        
        This method is responsible for the core server functionality and is run in a separate thread.
        """

        threading.Thread(target=self.update_handler).start()
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        while True:
            self.rlist, self.wlist, self.xlist = select.select([self.server_socket] + self.client_sockets, self.client_sockets, [])

            for client in self.rlist:
                if client is self.server_socket:
                    #accept new users
                    (connection, (ip, port)) = self.server_socket.accept()
                    self.client_sockets.append(connection)
                    print(f'new user connected {(ip, port)}')
                    self.socket_to_publickey[connection] = self.encryption.recv_public_key(self.recvall(connection, 271))
                    connection.send(self.encryption.get_public_key())

                    if not self.database.check_user(ip):
                        self.messages.append(('a', 0, '', [connection])) #authorization is needed
                        self.two_factor_auth.display_code()
                    else:
                        self.messages.append(('a', 1, '', [connection])) #authorization isn't needed

                    if self.block.get_block_state(): #updates the new user with the clients current block state
                        self.messages.append(('u', 1, '', [client]))
                    else:
                        self.messages.append(('u', 2, '', [client]))

                elif client in self.client_sockets:
                    # Receive messages from connected clients
                    if client in self.rlist:
                        try:
                            data_len = int(self.recvall(client, 8).decode())
                            ciphertext = self.recvall(client, data_len)
                        except:
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