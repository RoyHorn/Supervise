from server_utils import ActiveTime, Screenshot, Block, WebBlocker, Database, TwoFactorAuthentication, Encryption
import socket
import select
import datetime
import pickle
import threading
import time

class Server():
    '''handles the multiuser server'''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.block = Block()
        self.web_blocker = WebBlocker()
        self.database = Database()
        self.two_factor_auth = TwoFactorAuthentication()
        self.active_time = ActiveTime()
        self.active_time.start()
        self.database.create_time_limit_table()
        self.time_limit = self.database.get_time_limit()
        self.client_sockets = [] #contains all socket
        self.messages = [] #contains messages to be sent and recievers (msg, receivers)
        self.rlist = []
        self.wlist = []
        self.xlist = []
        self.BUFF_SIZE = 1024

    def send_messages(self):
        '''responsible for sending messages to the corrects clients'''
        #send messages correctly
        for type, cmmd, msg, recivers in self.messages:
            for reciver in recivers:
                if reciver in self.wlist:
                    if cmmd in (3,4,7): # specific handeling for already data already in byte format
                        #TODO add encryption
                        reciver.send((f'{type}{cmmd}{str(len(msg)).zfill(8)}').encode())
                        reciver.sendall(msg)
                        recivers.remove(reciver)
                    else:
                        #TODO add encryption
                        reciver.send(f'{type}{cmmd}{str(len(str(msg))).zfill(8)}{msg}'.encode())
                        recivers.remove(reciver)
            if not recivers:
                self.messages.remove((type, cmmd, msg, recivers))

    def handle_commands(self, cmmd, msg, client):
        '''responsible for giving the right response for every command'''
        if cmmd == '1': # start computer block
            self.messages.append(('u', 1, 'blocked', self.client_sockets.copy()))
            self.block.start()
        elif cmmd == '2': # end computer block
            self.messages.append(('u', 2, 'unblocked', self.client_sockets.copy()))
            self.block.end_block_func()
            self.block = Block()
        elif cmmd == '3': # take screenshot
            image = Screenshot().screenshot()
            self.messages.append(('r', 3, image, [client]))
        elif cmmd == '4': # request web blocker blocked list
            web_list = pickle.dumps(self.web_blocker.get_sites())
            self.messages.append(('r', 4, web_list, [client]))
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
        elif cmmd == '8': # update screentime limit
            #TODO think how to save the screentime limit
            self.messages.append(('r', 8, self.time_limit, [client]))
        elif cmmd == '9': # quit command
            self.database.change_time_limit(msg)
            self.time_limit = msg
            self.messages.append(('r', 9, self.time_limit, [client]))
        elif cmmd == '0':
            client.close()
            self.two_factor_auth.stop_code_display()
            self.client_sockets.remove(client)
        else:
            self.messages.append(('r', cmmd, msg, self.client_sockets.copy()))

    def handle_authorization(self, cmmd, code, client):
        if cmmd == '1':
            if self.two_factor_auth.verify_code(int(code)):
                self.messages.append(('a', 2, 'T', [client]))
                self.two_factor_auth.stop_code_display()
                client_ip, _ = client.getpeername()
                self.database.insert_user(client_ip)
            else:
                self.messages.append(('a', 2, 'F', [client]))
                self.client_sockets.remove(client)

    def update_handler(self):
        while True:
            time_now = datetime.datetime.now().time()
            if time_now.minute % 2 == 0:
                today_date = datetime.datetime.now().strftime("%Y-%m-%d")
                time_active = self.active_time.get_active_time()
                self.database.log_screentime(today_date, time_active)
            if not self.database.is_last_log_today():
                # means a day has passed and the server has reopened
                self.active_time.reset_active_time()
                self.messages.append(('u', 2, 'unblocked', self.client_sockets.copy()))
            if self.active_time.get_active_time() >= float(self.time_limit):
                self.messages.append(('u', 1, 'blocked', self.client_sockets.copy()))
                self.block.start()
            time.sleep(60)

    def serve(self):
        '''starts the server, responsible for handling current users and adding new ones'''
        #TODO add daily check for screentime, blocks and more...
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

                    if not self.database.check_user(ip):
                        self.messages.append(('a', 0, '', [connection]))
                        self.two_factor_auth.display_code()

                    if self.block.get_block_state():
                        self.messages.append(('u', 1, 'blocked', [client]))
                    else:
                        self.messages.append(('u', 2, 'unblocked', [client]))

                elif client in self.client_sockets:
                    #receive messages from connected clients
                    #TODO add decryption
                    type = client.recv(1).decode()
                    cmmd = client.recv(1).decode()

                    msg_length = int(client.recv(8).decode())
                    msg = client.recv(msg_length).decode()

                    if msg == 'quit':
                        self.client_sockets.remove(client)
                        client.close()
                        break
                    
                    if type == 'a':
                        self.handle_authorization(cmmd, msg, client)
                    elif type == 'r':
                        self.handle_commands(cmmd, msg, client)

            self.send_messages()                       

a = Server('0.0.0.0',8008)
a.serve()
