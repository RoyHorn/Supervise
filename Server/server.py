import datetime
import pickle
import select
import socket
import threading
import time
from server_utils import ActiveTime, Block, Database, Encryption, Screenshot, TwoFactorAuthentication, WebBlocker

class Server():
    """
    Handles the multiuser server functionality, including:
    - Accepting new client connections and managing the list of active clients
    - Handling various client commands such as starting/stopping computer block, taking screenshots, managing web blocker, and updating screentime data
    - Implementing two-factor authentication for new clients
    - Periodically updating the active time, web blocker, and enforcing screentime limits
    - Sending messages to the appropriate clients
    """

    def __init__(self, host, port):
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
        self.client_sockets = [] #contains all socket
        self.socket_to_publickey = {}
        self.messages = [] #contains messages to be sent and recievers (msg, receivers)
        self.rlist = []
        self.wlist = []
        self.xlist = []

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
        """
        Handles various client commands such as starting/stopping computer block, taking screenshots, managing web blocker, and updating screentime data.
        
        This method is responsible for processing different client commands and performing the appropriate actions. It updates the `self.messages` list with the necessary information to be sent to the clients.
        
        Args:
            cmmd (str): The command received from the client.
            msg (str): Any additional message or data associated with the command.
            client (socket.socket): The client socket that sent the command.
        """

        if cmmd == '1': # start computer block
            self.messages.append(('u', 1, '', self.client_sockets.copy()))
            self.block.start()
        elif cmmd == '2': # end computer block
            self.messages.append(('u', 2, '', self.client_sockets.copy()))
            self.block.end_block()
            self.block = Block()
        elif cmmd == '3': # take screenshot
            image = Screenshot().screenshot()
            self.messages.append(('r', 3, image, [client]))
        elif cmmd == '4': # request web blocker blocked list and browsing history
            web_list = pickle.dumps(self.web_blocker.get_sites())
            browsing_history = pickle.dumps(self.web_blocker.build_history_string())
            self.messages.append(('r', 4, web_list, [client]))
            self.messages.append(('r', 4, browsing_history, [client]))
        elif cmmd == '5': # add website to blocker
            self.messages.append(('r', 5, msg, [client]))
            self.web_blocker.add_website(msg)
        elif cmmd == '6': # remove website from blocker
            self.messages.append(('r', 6, msg, [client]))
            self.web_blocker.remove_website(msg)
        elif cmmd == '7': # request screentime data
            today_date = datetime.datetime.now().strftime("%Y-%m-%d")
            time_active = self.active_time.get_active_time()
            self.database.log_screentime(today_date, time_active)
            screentime_data = pickle.dumps(self.database.get_last_week_data())
            self.messages.append(('r', 7, screentime_data, [client]))
        elif cmmd == '8': # request screentime limit
            self.messages.append(('r', 8, self.time_limit, [client]))
        elif cmmd == '9': # update screentime limit
            self.database.change_time_limit(msg)
            self.time_limit = msg
            self.messages.append(('r', 9, self.time_limit, [client]))
        elif cmmd == '0': # quit
            client.close()
            self.two_factor_auth.stop_code_display()
            self.client_sockets.remove(client)
        else: #default response
            self.messages.append(('r', cmmd, msg, self.client_sockets.copy()))

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
            # in case the user entered the correct code
            self.messages.append(('a', 2, 'T', [client]))
            client_ip, _ = client.getpeername()
            self.database.insert_user(client_ip)
        else:
            # in case the user got rejected
            self.messages.append(('a', 2, 'F', [client]))
            self.client_sockets.remove(client)

        self.two_factor_auth.stop_code_display()

    def update_handler(self):
        """
        Updates the server's state at regular intervals, including:
        - Logging the active time for each client
        - Updating the web blocker file
        - Resetting the active time if a new day has started
        - Checking if the active time has exceeded the time limit and starting the block if so
        """
        while True:
            time_now = datetime.datetime.now().time()
            if time_now.minute % 1 == 0:
                self.active_time.log_active_time()
                self.web_blocker.update_file()
            if not self.database.is_last_log_today():
                # Means a day had passed
                self.active_time.reset_active_time()
                self.messages.append(('u', 2, '', self.client_sockets.copy())) # Unblock the user and update the block button text
            if self.active_time.get_active_time() >= float(self.time_limit):
                self.messages.append(('u', 1, '', self.client_sockets.copy())) # Block the user and update the block button text
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
        if cmmd not in (3,4,7): # 3: screenshot, 4: web blocker list, 7: screentime data, no need to encode
            data = str(data).encode()

        msg = f'{type}{cmmd}'.encode() + data

        ciphertext = self.encryption.encrypt(self.socket_to_publickey[client], msg)

        return ciphertext

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
                    self.socket_to_publickey[connection] = self.encryption.recv_public_key(connection.recv(271))
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
                    #receive messages from connected clients
                    data_len = int(client.recv(8).decode())
                    ciphertext = client.recv(data_len)

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

a = Server('0.0.0.0', 8008)
a.start()
