from threading import Thread
from win32api import GetLastInputInfo
from datetime import datetime
from PIL import ImageGrab
import time, keyboard, tkinter as tk, datetime as dt
import sqlite3

#color paletee
palette = {
    'background_color': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class ActiveTime(Thread):
    #TODO stop timer when block starts and resume when ends
    '''Responsible for counting active time on the computer'''
    def __init__(self):
        super().__init__()
        self.active_time = 0
        self.is_active = False
        self.state_change_delay = 1

    def update_is_active(self):
        '''updates the is_active argument of the class according to the active state of the computer, updates every ten second'''
        last_input = GetLastInputInfo()
        last_active = time.time()

        while True:
            time.sleep(1)
            if GetLastInputInfo() == last_input:
                #will run if user is not active
                not_active_delta = time.time()-last_active
                if not_active_delta > self.state_change_delay:
                    self.is_active = False
            else:
                #will run if user is active
                last_input = GetLastInputInfo()
                last_active = time.time()
                self.is_active = True

    def count_active_time(self):
        '''counts the active usage time of the machine, updates every second'''
        while True:
            if self.is_active:
                time.sleep(1)
                self.active_time += 1

    def run(self):
        '''runs two threads - one for changing the flag according to activity, the other for active time counting'''
        is_active_thread = Thread(target=self.update_is_active)
        count_time_thread = Thread(target=self.count_active_time)

        is_active_thread.start()
        count_time_thread.start()

        is_active_thread.join()
        count_time_thread.join()

    def reset_active_time(self):
        '''resets the active timer, will run every day change (every day at 00:00)'''
        self.active_time = 0

    def get_active_time(self):
        '''returns the active time'''
        return self.active_time

    def __str__(self):
        '''prints the current active time and active state'''
        return f'active time: {self.active_time} - is active: {self.is_active}'

class Database:
    def __init__(self):
        self.database = 'supervise_db.sqlite'

    def connect_to_db(self):
        conn = sqlite3.connect(self.database)
        return (conn ,conn.cursor())
    
    def create_user_table(self):
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                ip TEXT PRIMARY KEY NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def insert_user(self, ip):
        if self.check_user(ip):
            return
        self.create_user_table()
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            INSERT INTO users (ip) VALUES (?)
        ''', (ip,))
        conn.commit()
        conn.close()

    def check_user(self, ip):
        self.create_user_table()
        conn, cursor = self.connect_to_db()
        cursor.execute(f'''
            SELECT * FROM users
            WHERE ip=(?);
        ''', (ip,))
        user_exists = cursor.fetchone() is not None 

        conn.commit()
        conn.close()

        return user_exists

    def create_screentime_table(self):
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screentime (
                date DATE PRIMARY KEY NOT NULL,
                active_time TIME NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def log_screentime(self, date, active_time):
        if self.check_log(date):
            return
        self.create_screentime_table()
        conn, cursor = self.connect_to_db()
        cursor.execute(f'''
            INSERT INTO screentime (date, active_time)
                       VALUES (?, ?)
        ''', (date, active_time))
        conn.commit()
        conn.close()

    def check_log(self, date):
        self.create_user_table()
        conn, cursor = self.connect_to_db()
        cursor.execute(f'''
            SELECT * FROM screentime
            WHERE date=(?);
        ''', (date,))
        user_exists = cursor.fetchone() is not None 

        conn.commit()
        conn.close()

        return user_exists

class Block(Thread):
    '''Responsible for blocking the computer when needed'''
    def __init__(self):
        super().__init__()

    def run(self):
        '''starts the block'''
        self.disable_keyboard()
        self.setup_window()
        self.enable_keyboard() 

    def end_block(self):
        '''ends the block'''
        self.join(1)

    def setup_window(self):
        '''tkinter window setup'''
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.title("block")
        self.root['background'] = palette['background_color']

        #keeps the self.root on top
        self.root.wm_attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        logo = tk.Label(
            self.root,
            text="Supervise.",
            font=("CoolveticaRg-Regular",25),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        message = tk.Label(
            self.root,
            text="Buddy, you have reached your time limit...",
            font=("CoolveticaRg-Regular",60),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        limit = tk.Label(
            self.root,
            text=f"You can access your computer back tomorrow",
            font=("CoolveticaRg-Regular",30),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        tk.Button(self.root,text = 'exit', command=self.root.destroy).place(rely=0.95,relx=0.12, anchor= 'center')
        message.place(relx = 0.5, rely = 0.45, anchor = 'center')
        limit.place(relx = 0.5, rely = 0.55, anchor = 'center')    
        logo.place(relx = 0.5, rely = 0.9, anchor = 'center')

        self.root.after(self.calculate_ms_delta(), self.root.destroy)
        self.root.mainloop()

    def calculate_ms_delta(self):
        '''calculates the ms delta until next day in order to automatically
          release the block when next day arrives'''
        now = datetime.now()
        tomorrow = (now + dt.timedelta(1)).replace(hour=0, minute=0, second=0)

        delta = (tomorrow-now).seconds
        
        return delta*1000

    def disable_keyboard(self):
        '''disables keyboard'''
        for i in range(150):
            keyboard.block_key(i)
        
    def enable_keyboard(self):
        '''enables keyboard'''
        for i in range(150):
            keyboard.unblock_key(i)

class TwoFactorAuthentication():
    def __init__():
        pass

class WebBlocker:
    '''responsible for blocking access to specific web pages using os hosts files'''
    def __init__(self):
        self.path = 'C:/Windows/system32/drivers/etc/hosts'
        self.redirect = '127.0.0.1'
        self.blocked_sites = self.get_sites()

    def get_sites(self): #TODO
        with open(self.path,'r') as f:
            raw_data = f.read()

            if len(raw_data)>0:
                # Split the raw data into lines
                lines = raw_data.strip().split('\n')

                # Extract URLs from each line
                urls = [line.split()[1] for line in lines]
                return urls

        return []


    def update_file(self):
        '''responsible for updating the hosts file after every change'''
        f = open(self.path, 'w')
        for domain in self.blocked_sites:
            f.write(f'\n{self.redirect}  {domain}    #added using Supervise.')
        f.close()

    def add_website(self, domain):
        '''responsible for adding pages to the block list'''
        self.blocked_sites.append(domain)
        print(self.blocked_sites)
        self.update_file()

    def remove_website(self, domain):
        '''responsible for removing sites from the block site'''
        self.blocked_sites.remove(domain)
        self.update_file()

class Screenshot:
    '''responsible for taking screenshot and translating to bytes'''
    def screenshot(self):
        pic = ImageGrab.grab()
        return pic.tobytes()