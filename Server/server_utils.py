from threading import Thread
import threading
from win32api import GetLastInputInfo
from datetime import datetime, timedelta
from PIL import ImageGrab
import time, keyboard, tkinter as tk, datetime as dt
import sqlite3
import pyotp
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import pickle
import gzip

#color paletee
palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class ActiveTime(Thread):
    #TODO stop timer when block starts and resume when ends
    '''Responsible for counting active time on the computer'''
    def __init__(self):
        super().__init__()
        self.total_time_active = Database().get_today_active_time()*3600
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
                self.total_time_active += 1

    def run(self):
        '''runs two threads - one for changing the flag according to activity, the other for active time counting'''
        is_active_thread = Thread(target=self.update_is_active)
        count_time_thread = Thread(target=self.count_active_time)

        is_active_thread.start()
        count_time_thread.start()

        is_active_thread.join()
        count_time_thread.join()

    def reset_active_time(self):
        '''log last day and resets the active timer, will run every day change (every day at 00:00)'''
        Database().log_screentime(datetime.now().strftime("%Y-%m-%d"),0)
        self.total_time_active = 0

    def get_active_time(self):
        '''returns the active time'''
        return float(self.total_time_active/3600)
    
    def __str__(self):
        '''prints the current active time and active state'''
        return f'active time: {self.total_time_active} - is active: {self.is_active}'

class Database:
    def __init__(self):
        self.database = 'supervise_db.sqlite'

    def connect_to_db(self):
        '''creates connection to the database'''
        conn = sqlite3.connect(self.database)
        return (conn ,conn.cursor())
    
    def create_user_table(self):
        '''creates the user table'''
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                ip TEXT PRIMARY KEY NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def insert_user(self, ip):
        '''inserts a new user to the users table'''
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
        '''checks if a certain user is in the users table'''
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
        '''creates screentime table if not exists'''
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screentime (
                date DATE PRIMARY KEY NOT NULL,
                active_time REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def log_screentime(self, date, active_time):
        self.create_screentime_table()
        
        conn, cursor = self.connect_to_db()

        # Use INSERT OR REPLACE with explicit conflict resolution
        cursor.execute('''
            INSERT OR REPLACE INTO screentime (date, active_time)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET active_time=excluded.active_time
        ''', (date, active_time))

        conn.commit()
        conn.close()

    def check_log(self, date):
        '''checks if there was a log in the last day'''
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
    
    def get_last_week_data(self):
        self.create_screentime_table()
        seven_days_ago = datetime.now()-timedelta(days=7)
        seven_days_ago.strftime("%Y-%m-%d")
        result = ''

        try:
            self.create_screentime_table()
            conn, cursor = self.connect_to_db()
            cursor.execute('''
                SELECT * FROM screentime WHERE date > ?
            ''', (seven_days_ago,))
            result = cursor.fetchall()

            conn.close()
        except:
            pass

        return result
    
    def get_today_active_time(self):
            '''returns the total active time for today'''
            self.create_screentime_table()
            conn, cursor = self.connect_to_db()

            try:
                today_date = datetime.now().strftime("%Y-%m-%d")
                cursor.execute('''
                    SELECT active_time FROM screentime WHERE date = ?
                ''', (today_date,))
                result = cursor.fetchone()

                if result:
                    return result[0]  # Returning the active time for today
                else:
                    return 0  # If no entry for today, return 0 as default
            except sqlite3.Error as e:
                return 0
            finally:
                conn.close()
    
    def is_last_log_today(self):
        '''returns True if the last log entry is today, False otherwise'''
        self.create_screentime_table()
        conn, cursor = self.connect_to_db()

        try:
            cursor.execute('''
                SELECT MAX(date) FROM screentime
            ''')
            last_log_date = cursor.fetchone()[0]
            
            if last_log_date is not None:
                last_log_date = datetime.strptime(last_log_date, "%Y-%m-%d").date()
                
                # Check if the last log date is today
                return last_log_date == datetime.now().date()
                
            else:
                return False
        except sqlite3.Error as e:
            return False
        finally:
            conn.close()

    def create_time_limit_table(self):
        '''creates the time limit table'''
        conn, cursor = self.connect_to_db()

        # Create the timelimit table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timelimit (
                lim REAL NOT NULL
            )
        ''')

        # Commit changes and close the connection
        conn.commit()
        conn.close()

    def get_time_limit(self):
        self.create_screentime_table()
        conn, cursor = self.connect_to_db()

        # Assuming that the table has already been created using create_time_limit_table method
        cursor.execute('SELECT lim FROM timelimit')
        result = cursor.fetchone()

        if result:
            time_limit = result[0]
        else:
            time_limit = 24

        conn.close()
        return time_limit

    def change_time_limit(self, new_limit):
        '''changes the time limit in the timelimit table'''
        self.create_time_limit_table()
        conn, cursor = self.connect_to_db()

        # Check if the table is empty
        cursor.execute('SELECT COUNT(*) FROM timelimit')
        count = cursor.fetchone()[0]

        if count == 0:
            # If the table is empty, insert a new row with the new limit value
            cursor.execute('INSERT INTO timelimit (lim) VALUES (?)', (new_limit,))
        else:
            # Update the existing row with the new limit value
            cursor.execute('UPDATE timelimit SET lim = ? WHERE rowid = 1', (new_limit,))

        # Commit changes and close the connection
        conn.commit()
        conn.close()

class Block(Thread):
    '''Responsible for blocking the computer when needed'''
    def __init__(self):
        super().__init__()
        self.block_state = False
        self.end_block_flag = False
        self.block_lock = threading.Lock()

    def run(self):
        '''starts the block'''
        self.end_block_flag = False
        self.block_state = True
        self.disable_keyboard()
        self.setup_window()
        self.enable_keyboard() 

    def end_block_func(self):
        '''responsible for ending the block when requested by the client'''
        #TODO add thread killer in order to be able to re run the thread later
        with self.block_lock:
            self.end_block_flag = True
            self.block_state = False

    def setup_window(self):
        def close():
            self.root.destroy()
            self.enable_keyboard()

        '''tkinter block window setup'''
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.title("block")
        self.root['background'] = palette['background_color']

        # keeps the self.root on top
        self.root.wm_attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        logo = tk.Label(
            self.root,
            text="Supervise.",
            font=("CoolveticaRg-Regular", 25),
            bg=palette['background_color'],
            fg=palette['text_color']
        )

        message = tk.Label(
            self.root,
            text="Buddy, you have reached your time limit...",
            font=("CoolveticaRg-Regular", 60),
            bg=palette['background_color'],
            fg=palette['text_color']
        )

        limit = tk.Label(
            self.root,
            text="You can access your computer back tomorrow",
            font=("CoolveticaRg-Regular", 30),
            bg=palette['background_color'],
            fg=palette['text_color']
        )

        tk.Button(self.root, text='exit', command=close).place(rely=0.95, relx=0.12, anchor='center')
        message.place(relx=0.5, rely=0.45, anchor='center')
        limit.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        self.root.after(self.calculate_ms_delta(), self.root.destroy)

        while not self.end_block_flag:
            self.root.update()
            self.root.update_idletasks()

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

    def get_block_state(self):
        return self.block_state

class Encryption():
    def __init__(self):
        self.key = RSA.generate(1024)
        self.public_key = self.key.publickey()
        self.private_key = self.key

    def encrypt(self, key, data):
        cipher = PKCS1_OAEP.new(key)
        chunk_size = 86  # Adjust this value based on your key size
        encrypted_data = b""

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_data += encrypted_chunk

        return encrypted_data
    
    def decrypt(self, ciphertext):
        decrypt_cipher = PKCS1_OAEP.new(self.private_key)
        chunk_size = 128  # Adjust this value based on your key size
        decrypted_message = b""

        for i in range(0, len(ciphertext), chunk_size):
            chunk = ciphertext[i:i + chunk_size]
            decrypted_chunk = decrypt_cipher.decrypt(chunk)
            decrypted_message += decrypted_chunk

        decrypted_message = decrypted_message.decode()
        type = decrypted_message[:1]
        cmmd = decrypted_message[1:2]
        msg = decrypted_message[2:]

        return type, cmmd, msg
    
    def get_public_key(self):
        pem_key = self.public_key.export_key()
        return pem_key
    
    def recv_public_key(self, pem_key):
        return RSA.import_key(pem_key)

class TwoFactorAuthentication(Thread):
    def __init__(self):
        super().__init__()
        self.secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.secret)
        self.show = False

    def get_time_remaining(self):
        return self.totp.interval - datetime.now().timestamp() % self.totp.interval

    def generate_authenication_code(self):
        return self.totp.now()

    def verify_code(self, input_code):
        return self.totp.verify(input_code)

    def display_window(self):
        self.show = True
        window = tk.Tk()
        window.title('Code Screen')
        window.configure
        window.wm_attributes("-topmost", True)
        window.protocol("WM_DELETE_WINDOW", lambda: self.stop_code_display())
        window['background'] = palette['blue_bg']

        frame = tk.Frame(window, bg=palette['blue_bg'])
        frame.pack(pady=10)

        # Create a label to display the code
        label = tk.Label(frame, text=f"Two Factor Authenication Code:", font=("Calibri", 20), fg=palette['text_color'], bg=palette['blue_bg'], padx=20)
        code_label = tk.Label(frame, text=f"", font=("Calibri", 50), fg=palette['text_color'], bg=palette['blue_bg'], padx=20)
        label.pack()
        code_label.pack()

        # Run the Tkinter event loop
        while self.show:
            code_label.config(text=self.generate_authenication_code())
            window.update()
            window.update_idletasks()

    def display_code(self):
        if not self.show:
            window_thread = threading.Thread(target=self.display_window)
            window_thread.start()

    def stop_code_display(self):
        if self.show:
            self.show = False #stops the current instance of window

class WebBlocker:
    '''responsible for blocking access to specific web pages using os hosts files'''
    def __init__(self):
        self.path = 'C:/Windows/system32/drivers/etc/hosts'
        self.redirect = '127.0.0.1'
        self.blocked_sites = self.get_sites()

    def get_sites(self):
        '''gets the sites list from the hosts os file'''
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
        self.update_file()

    def remove_website(self, domain):
        '''responsible for removing sites from the block site'''
        self.blocked_sites.remove(domain)
        self.update_file()

class Screenshot:
    '''responsible for taking screenshot and translating to bytes'''
    def screenshot(self):
        pic = ImageGrab.grab()
        pic_bytes = pic.tobytes()
        compressed_pic = gzip.compress(pic_bytes)
        return pickle.dumps(compressed_pic)

# conn, cursor = Database().connect_to_db()
# cursor.execute('''
#     DELETE FROM users
# ''')
# conn.commit()
# conn.close()