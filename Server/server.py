import socket
import select
from server_utils import ActiveTime, Screenshot, Block, WebBlocker

class Server():
    '''handles the multiuser server'''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.block = Block()
        self.web_blocker = WebBlocker()
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
                    if cmmd == 3 or cmmd == 4: # specific handeling for images
                        reciver.send((f'{type}{cmmd}{str(len(msg)).zfill(8)}').encode())
                        reciver.sendall(msg)
                        recivers.remove(reciver)
                    else:
                        reciver.send(f'{type}{cmmd}{str(len(msg)).zfill(8)}{msg}'.encode())
                        recivers.remove(reciver)
            if not recivers:
                self.messages.remove((type, cmmd, msg,recivers))

    def handle_commands(self, cmmd, msg, client):
        '''responsible for giving the right response for every command'''
        if cmmd == '1': # start computer block
            self.messages.append(('u', 1, 'blocked', self.client_sockets.copy()))
            self.block.start()
        elif cmmd == '2': # end computer block
            self.messages.append(('u', 2, 'unblocked', self.client_sockets.copy()))
        elif cmmd == '3': # take screenshot
            image = Screenshot().screenshot()
            self.messages.append(('r', 3, image, [client]))
        elif cmmd == '4':
            raw_data = self.web_blocker.get_data()
            self.messages.append(('r', 4, raw_data, [client]))
        elif cmmd == '5':
            self.messages.append(('u', 5, msg, self.client_sockets.copy()))
            self.web_blocker.add_website(msg)
        elif cmmd == '6':
            self.messages.append(('u', 6, msg, self.client_sockets.copy()))
            self.web_blocker.remove_website(msg)
        else:
            self.messages.append(('r', cmmd, msg, self.client_sockets.copy()))

    def serve(self):
        '''starts the server, responsible for handling current users and adding new ones'''
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        active_time = ActiveTime()
        active_time.start()

        while True:
            self.rlist, self.wlist, self.xlist = select.select([self.server_socket] + self.client_sockets, self.client_sockets, [])

            for client in self.rlist:
                if client is self.server_socket:
                    #accept new users
                    #TODO 2FA will be added here
                    (connection, addr) = self.server_socket.accept()
                    self.client_sockets.append(connection)
                    print(f'new user connected {addr}')
                elif client in self.client_sockets:
                    #receive messages from connected clients
                    cmmd = client.recv(1).decode()

                    msg_length = int(client.recv(8).decode())
                    msg = client.recv(msg_length).decode()

                    if msg == 'quit':
                        self.client_sockets.remove(client)
                        client.close()
                        break

                    self.handle_commands(cmmd, msg, client)

            self.send_messages()                       

a = Server('0.0.0.0',8008)
a.serve()
