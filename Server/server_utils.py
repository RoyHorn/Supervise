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
import platform
import os

#color paletee
palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class ActiveTime(Thread):
    '''Responsible for counting active time on the computer'''
    def __init__(self):
        super().__init__()
        self.total_time_active = Database().get_today_active_time()*3600
        self.is_active = False
        self.STATE_CHANGE_DELAY = 1

    def update_is_active(self):
        """
        Updates the `is_active` attribute of the `ActiveTime` class based on the user's activity on the computer. This method runs in a separate thread and checks the user's activity every second, updating the `is_active` attribute accordingly.
        
        If the user is not active for more than `self.STATE_CHANGE_DELAY` seconds, the `is_active` attribute is set to `False`. If the user becomes active again, the `is_active` attribute is set to `True`.
        """
        last_input = GetLastInputInfo()
        last_active = time.time()

        while True:
            time.sleep(1)
            if GetLastInputInfo() == last_input:
                #will run if user is not active
                not_active_delta = time.time()-last_active
                if not_active_delta > self.STATE_CHANGE_DELAY:
                    self.is_active = False
            else:
                #will run if user is active
                last_input = GetLastInputInfo()
                last_active = time.time()
                self.is_active = True

    def count_active_time(self):
        """
        Counts the active usage time of the machine, updating the total active time every second while the user is active.
        
        This method is called in a separate thread by the `ActiveTime` class to continuously monitor the user's activity and update the `total_time_active` attribute accordingly. If the user is active, the `total_time_active` is incremented by 1 second every second. If the user is inactive for more than `self.STATE_CHANGE_DELAY` seconds, the `is_active` attribute is set to `False`.
        """
        while True:
            if self.is_active:
                time.sleep(1)
                self.total_time_active += 1

    def run(self):
        """
        Runs two threads - one for changing the `is_active` flag according to user activity, and the other for counting the active time.
        
        The `update_is_active` thread continuously monitors the user's activity and updates the `is_active` attribute accordingly. If the user is inactive for more than `self.STATE_CHANGE_DELAY` seconds, the `is_active` attribute is set to `False`. If the user becomes active again, the `is_active` attribute is set to `True`.
        
        The `count_active_time` thread continuously increments the `total_time_active` attribute by 1 second every second while the user is active (i.e., `is_active` is `True`).
        
        Both threads are started and joined in this method to ensure they run concurrently.
        """
        is_active_thread = Thread(target=self.update_is_active)
        count_time_thread = Thread(target=self.count_active_time)

        is_active_thread.start()
        count_time_thread.start()

        is_active_thread.join()
        count_time_thread.join()

    def log_active_time(self):
        """
        Logs the active time for the current day to the database.
        
        This method is called to record the total active time for the current day in the database. It retrieves the current date, calls the `get_active_time()` method to get the total active time, and then logs this information to the database using the `log_screentime()` method of the `Database` class.
        """
        today_date = datetime.now().strftime("%Y-%m-%d")
        Database().log_screentime(today_date, self.get_active_time())

    def reset_active_time(self):
        """
        Resets the active time counter and logs the total active time for the previous day to the database.
        
        This method is called daily at midnight (00:00) to reset the `total_time_active` attribute to 0 and log the total active time for the previous day to the database using the `log_screentime()` method of the `Database` class.
        """
        Database().log_screentime(datetime.now().strftime("%Y-%m-%d"),0)
        self.total_time_active = 0

    def get_active_time(self) -> float:
        """
        Returns the total active time in hours.
        
        This method calculates and returns the total active time in hours by dividing the `total_time_active` attribute by 3600 (the number of seconds in an hour).
        """
        return float(self.total_time_active/3600)
        
    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        """
        return f'active time: {self.total_time_active} - is active: {self.is_active}'

class Database:
    def __init__(self):
        self.database = 'supervise_db.sqlite'

    def connect_to_db(self) -> tuple:
        """
        Connects to the SQLite database specified in the `database` attribute.
        
        This method is used to establish a connection to the SQLite database that is used to store the user's active time data. It is an internal implementation detail of the `Database` class and is not intended to be called directly by external code.

        Returns:
            (conn, conn.cursor()) (Tuple): A tuple containing the connection object and the cursor object.
        """
        conn = sqlite3.connect(self.database)
        return (conn ,conn.cursor())
    
    def create_user_table(self):
        """
        Creates a table named "users" in the SQLite database if it doesn't already exist. The table has a single column named "ip" which is used as the primary key and is required to not be null.
        
        This method is an internal implementation detail of the `Database` class and is not intended to be called directly by external code.
        """
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                ip TEXT PRIMARY KEY NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def insert_user(self, ip: str):
        """
        Inserts a new user into the users table in the SQLite database.
        
        This method checks if the given IP address already exists in the users table. If it does not, it creates the users table if it doesn't already exist, and then inserts a new row with the provided IP address.
        
        Args:
            ip (str): The IP address of the new user to be inserted.
        """
        if self.check_user(ip):
            return
        self.create_user_table()
        conn, cursor = self.connect_to_db()
        cursor.execute('''
            INSERT INTO users (ip) VALUES (?)
        ''', (ip,))
        conn.commit()
        conn.close()

    def check_user(self, ip: str) -> bool:
        """
        Checks if a user with the given IP address exists in the users table of the SQLite database.
        
        It is used to determine if a user with the given IP address already exists in the database.

        Args:
            ip (str): The IP address of the user to check.
        
        Returns:
            user_exists (Boolean): True if the user with the given IP address exists in the database, False otherwise.
        """
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
        """
        Creates a table named "screentime" in the SQLite database if it doesn't already exist. The table has two columns:
        
        - "date": A primary key column of type DATE that stores the date.
        - "active_time": A REAL column that stores the active time for the given date.
        
        This method is used to ensure the existence of the screentime table in the database, which is used to store user activity data.
        """

        conn, cursor = self.connect_to_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screentime (
                date DATE PRIMARY KEY NOT NULL,
                active_time REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def log_screentime(self, date: datetime.date, active_time: float):
        """
        Logs the active time for a given date in the "screentime" table of the SQLite database.
        
        If a record for the given date already exists, it will be updated with the new active_time value. If the record does not exist, a new one will be inserted.
        
        Args:
            date (datetime.date): The date for which to log the active time.
            active_time (float): The active time in seconds for the given date.
        """
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
    
    def get_last_week_data(self) -> list[tuple]:
        """
        Retrieves the screentime data for the last 7 days from the SQLite database.
        
        This method creates the "screentime" table if it doesn't already exist, and then executes a SQL query to fetch all records where the date is in the last 7 days.
        The result is returned as a list of tuples, where each tuple represents a row in the "screentime" table.
        
        Returns:
            result (list): A list of tuples, where each tuple represents a row in the "screentime" table for the last 7 days.
        """
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
    
    def get_today_active_time(self) -> float:
            """
            Returns the total active time for today.
            
            This method creates the "screentime" table if it doesn't already exist,
            and then executes a SQL query to fetch the active_time value for the current date.
            If a record exists, the active_time value is returned. If no record exists, 0 is returned.
            
            Returns:
                result (float): The total active time for today in seconds.
            """
            self.create_screentime_table()
            conn, cursor = self.connect_to_db()

            try:
                today_date = datetime.now().strftime("%Y-%m-%d")
                cursor.execute('''
                    SELECT active_time FROM screentime WHERE date = ?
                ''', (today_date,))
                result = cursor.fetchone()

                if result:
                    return result[0]
                else:
                    return 0
            finally:
                conn.close()
    
    def is_last_log_today(self) -> bool:
        """
        Returns True if the last log entry is today, False otherwise.
        
        This method creates the "screentime" table if it doesn't already exist, and then
        executes a SQL query to fetch the maximum date from the "screentime" table.
        If the last log date is not None, it checks if the last log date is the same as
        the current date. If so, it returns True, otherwise it returns False.
        """
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
        """
        Creates the "timelimit" table in the database if it doesn't already exist.
        
        This method establishes a connection to the database, checks if the "timelimit" table
        exists, and if not, creates the table with a single column "lim" of type REAL.
        The changes are then committed to the database and the connection is closed.
        """
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

    def get_time_limit(self) -> float:
        """
        Returns the time limit value from the "timelimit" table in the database.
        """
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

    def change_time_limit(self, new_limit: float):
        """
        Changes the time limit value in the "timelimit" table of the database.
        
        This method first checks if the "timelimit" table exists, and creates it if it doesn't.
        It then checks if the table is empty, if it is, a new row is inserted with the new limit value.
        If the table is not empty, the existing row is updated with the new limit value.
        
        The changes are then committed to the database and the connection is closed.
        
        Args:
            new_limit (float): The new time limit value to be set.
        """
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
    """
    Responsible for blocking the computer when needed. This class manages the state of the computer block, including setting up a full-screen window with a message informing the user that their time limit has been reached, and disabling/enabling the keyboard.
    
    The `Block` class is a subclass of `Thread`, which allows it to run in a separate thread from the main application. This ensures that the blocking functionality does not block the main application.
    
    The class has the following methods:
    
    - `__init__()`: Initializes the block state, end block flag, and a lock for thread-safe access.
    - `run()`: Starts the block by disabling the keyboard, setting up the block window, and enabling the keyboard.
    - `end_block()`: Ends the block by setting the end block flag and resetting the block state.
    - `setup_window()`: Sets up the full-screen block window with a message and logo.
    - `calculate_ms_delta()`: Calculates the number of milliseconds until the next day, so that the block can be automatically released.
    - `disable_keyboard()`: Disables the keyboard by blocking all keys.
    - `enable_keyboard()`: Enables the keyboard by unblocking all keys.
    - `get_block_state()`: Returns the current block state.
    """

    def __init__(self):
        super().__init__()
        self.block_state = False
        self.end_block_flag = False
        self.block_lock = threading.Lock()

    def run(self):
        """
        Starts the block by disabling the keyboard, and setting up the block window.
        """
        self.end_block_flag = False
        self.block_state = True
        self.disable_keyboard()
        self.setup_window()
        self.enable_keyboard() 

    def end_block(self):
        """
        Ends the block when requested by the client. This method sets the `end_block_flag` to `True` and the `block_state` to `False`, allowing the block to be released. 
        The method uses a lock to ensure thread-safe access to the block state.
        """
        with self.block_lock:
            self.end_block_flag = True
            self.block_state = False

    def setup_window(self):
        """
        Sets up the full-screen block window with a message and logo. This method is responsible for creating the Tkinter window, setting its attributes, and placing the message and logo labels on the window. The window is kept on top of other windows and cannot be closed by the user.
        
        The window is set to automatically destroy itself after the calculated number of milliseconds until the next day, using the `self.calculate_ms_delta()` method.
        
        This method runs in a loop, updating the window until the `self.end_block_flag` is set to `True`, indicating that the block should be ended.
        """
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.title("block")
        self.root['background'] = palette['blue_bg']

        # keeps the self.root on top
        self.root.wm_attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        logo = tk.Label(
            self.root,
            text="Supervise.",
            font=("CoolveticaRg-Regular", 25),
            bg=palette['blue_bg'],
            fg=palette['text_color']
        )

        message = tk.Label(
            self.root,
            text="Buddy, you have reached your time limit...",
            font=("CoolveticaRg-Regular", 60),
            bg=palette['blue_bg'],
            fg=palette['text_color']
        )

        limit = tk.Label(
            self.root,
            text="You can access your computer back tomorrow",
            font=("CoolveticaRg-Regular", 30),
            bg=palette['blue_bg'],
            fg=palette['text_color']
        )

        # tk.Button(self.root, text='exit', command=close).place(rely=0.95, relx=0.12, anchor='center')
        message.place(relx=0.5, rely=0.45, anchor='center')
        limit.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        self.root.after(self.calculate_ms_delta(), self.root.destroy)

        while not self.end_block_flag:
            self.root.update()
            self.root.update_idletasks()

    def calculate_ms_delta(self) -> int:
        """
        Calculates the number of milliseconds until the next day, in order to automatically release the block when the next day arrives.
        
        Returns:
            int: The number of milliseconds until the next day.
        """

        # Get the current time and date
        now = datetime.now()
        tomorrow = (now + dt.timedelta(1)).replace(hour=0, minute=0, second=0)

        # Calculate the number of seconds until the next day
        delta = (tomorrow-now).seconds
        
        return delta*1000

    def disable_keyboard(self):
        """
        Disables the keyboard by blocking all keys.
        
        This function iterates through the range of key codes (0-149) and blocks each key using the `keyboard.block_key()` function. This effectively disables the entire keyboard, preventing the user from interacting with the system.
        """
        for i in range(150):
            keyboard.block_key(i)
        
    def enable_keyboard(self):
        """
        Enables the keyboard by unblocking all keys that were previously blocked.
        
        This function iterates through the range of key codes (0-149) and unblocks each key using the `keyboard.unblock_key()` function. This effectively re-enables the entire keyboard, allowing the user to interact with the system.
        """
        for i in range(150):
            keyboard.unblock_key(i)

    def get_block_state(self) -> bool:
        """
        Returns the current block state.
        """
        return self.block_state

class Encryption():
    """
    The `Encryption` class provides a simple interface for encrypting and decrypting data using RSA encryption.
    
    The class generates a 1024-bit RSA key pair on initialization, and provides methods to encrypt and decrypt data using the public and private keys, respectively.
    
    The `encrypt()` method takes a key (either the public key or the private key) and some data, and returns the encrypted data.
    The `decrypt()` method takes the encrypted ciphertext and returns the original plaintext message, along with the message type and command.
    
    The `get_public_key()` method returns the public key as a PEM-encoded string
    The `recv_public_key()` method imports a public key from a PEM-encoded string.
    """
    def __init__(self):
        self.key = RSA.generate(1024)
        self.public_key = self.key.publickey()
        self.private_key = self.key

    def encrypt(self, key, data: bytes) -> bytes:
        """
        Encrypts the given data using the provided RSA key.
        
        The data is encrypted in chunks of 86 bytes to avoid exceeding the maximum plaintext size for the RSA key. The encrypted chunks are then concatenated and returned as the final encrypted data.
        
        Args:
            key (Crypto.PublicKey.RSA.RsaKey): The RSA key to use for encryption.
            data (bytes): The data to be encrypted.
        
        Returns:
            encrypted_data (bytes): The encrypted data.
        """
        cipher = PKCS1_OAEP.new(key)
        chunk_size = 86 
        encrypted_data = b""

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_data += encrypted_chunk

        return encrypted_data
    
    def decrypt(self, ciphertext: bytes) -> tuple[str, str, str]:
        """
        Decrypts the provided ciphertext using the private RSA key.
        
        The ciphertext is decrypted in chunks of 128 bytes to avoid exceeding the maximum ciphertext size for the RSA key.
        The decrypted chunks are then concatenated and returned as the final decrypted message.
        
        The decrypted message is then split into the message type, command, and message content.
        
        Args:
            ciphertext (bytes): The encrypted ciphertext to be decrypted.
        
        Returns:
            type (str): The type of the decrypted message.
            cmmd (str): The command of the decrypted message.
            msg (str): The content of the decrypted message.
        """
        decrypt_cipher = PKCS1_OAEP.new(self.private_key)
        chunk_size = 128
        decrypted_message = b""

        for i in range(0, len(ciphertext), chunk_size):
            chunk = ciphertext[i:i + chunk_size]
            decrypted_chunk = decrypt_cipher.decrypt(chunk)
            decrypted_message += decrypted_chunk

        decrypted_message = decrypted_message.decode()
        type = decrypted_message[:1]
        cmmd = decrypted_message[1:2]
        msg = decrypted_message[2:]

        return (type, cmmd, msg)
    
    def get_public_key(self) -> bytes:
        """
        Returns the public RSA key as a byte string.
        """
        return self.public_key.export_key()
    
    def recv_public_key(self, pem_key: bytes):
        """
        Imports an RSA public key from a PEM-encoded string.
        
        Args:
            pem_key (bytes): The PEM-encoded RSA public key.
        
        Returns:
            RSA Key : The imported RSA public key object.
        """
        return RSA.import_key(pem_key)

class TwoFactorAuthentication(Thread):
    """
    Implements a two-factor authentication (2FA) system using a Time-based One-Time Password (TOTP) algorithm.
    
    The `TwoFactorAuthentication` class generates a random secret key and uses it to create a TOTP object.
    It provides methods to generate and verify 2FA codes, as well as to display the current 2FA code in a Tkinter window.
    
    The `generate_authenication_code()` method generates the current 2FA code based on the secret key and the current time.
    The `verify_code()` method verifies a provided 2FA code against the current code generated by the TOTP object.
    The `create_code_display()` method creates a Tkinter window that continuously displays the current 2FA code.
    The `display_code()` method starts the 2FA code display window in a separate thread.
    The `stop_code_display()` method stops the 2FA code display window.
    """
    def __init__(self):
        super().__init__()
        self.secret = pyotp.random_base32() # Generate a random base32 secret key
        self.totp = pyotp.TOTP(self.secret) # Create a TOTP (Time-based One-Time Password) object using the secret key
        self.show = False # Variable to control whether to show the TOTP

    def generate_authenication_code(self) -> str:
        """
        Generates the current Time-based One-Time Password (TOTP) code based on the secret key.
        
        Returns:
            str: The current TOTP code.
        """
        return self.totp.now()

    def verify_code(self, input_code: str) -> bool:
        """
        Verifies the provided Time-based One-Time Password (TOTP) code against the current TOTP code generated by the TOTP object.
        
        Args:
            input_code (str): The TOTP code to be verified.
        
        Returns:
            bool: True if the provided code matches the current TOTP code, False otherwise.
        """
        return self.totp.verify(input_code)

    def create_code_display(self):
        """
        Creates a Tkinter window that continuously displays the current Time-based One-Time Password (TOTP) code.
        
        The `create_code_display()` method creates a Tkinter window with a label that displays the current TOTP code.
        The window is set to be always on top, and the window's close button is configured to call the `stop_code_display()` method to stop the code display.
        
        The method enters a loop that updates the code label with the current TOTP code generated by the `generate_authenication_code()` method. The loop continues as long as the `show` flag is set to `True`.
        """
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
        """
        Displays the current Time-based One-Time Password (TOTP) code in a Tkinter window.
        """
        if not self.show:
            window_thread = threading.Thread(target=self.create_code_display)
            window_thread.start()

    def stop_code_display(self):
        """
        Stops the continuous display of the current Time-based One-Time Password (TOTP) code in the Tkinter window.
        
        This method sets the `show` flag to `False`, which causes the loop in the `create_code_display()` method to exit, effectively stopping the code display.
        """
        if self.show:
            self.show = False #stops the current instance of window

class WebBlocker:
    """
    The `WebBlocker` class provides functionality to manage a hosts file for blocking websites.
    
    The class has the following methods:
    
    - `get_hosts_file_location()`: Returns the location of the hosts file based on the operating system.
    - `get_sites()`: Reads the hosts file and extracts the list of blocked websites.
    - `update_file()`: Updates the hosts file with the current list of blocked websites.
    - `add_website(domain)`: Adds a new website to the block list and updates the hosts file.
    - `remove_website(domain)`: Removes a website from the block list and updates the hosts file.
    - `extract_history(history_db)`: Extracts the browsing history from the Chrome browser's history database.
    - `build_history_string()`: Builds a dictionary of the browsing history.
    """
    
    def __init__(self):
        self.path = self.get_hosts_file_location()
        self.redirect = '127.0.0.1'
        self.blocked_sites = self.get_sites()

    def get_hosts_file_location(self) -> str:
        """
        Returns the location of the hosts file based on the operating system.
        
        This method checks the current operating system and returns the appropriate file path for the hosts file.
        It supports Windows, Linux, and macOS (Darwin) operating systems.
        If the operating system is not supported, it raises an OSError exception.
        
        Returns:
            str: The file path of the hosts file.
        
        Raises:
            OSError: If the operating system is not supported.
        """
        system = platform.system()
        if system == "Windows":
            return r'C:\Windows\System32\drivers\etc\hosts'
        elif system == "Linux" or system == "Darwin":
            return '/etc/hosts'
        else:
            raise OSError("Unsupported operating system")

    def get_sites(self) -> list:
        """
        Gets the list of blocked websites from the hosts file.
        
        This method reads the contents of the hosts file and extracts the URLs of the blocked websites. It returns a list of these URLs.
        
        Returns:
            list: A list of blocked website URLs.
        """
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
        """
        Updates the hosts file by writing the blocked websites and their redirect address to the file.
        
        This method iterates through the list of blocked websites stored in `self.blocked_sites` and writes each one to the hosts file, prefixed with the redirect address `self.redirect`.
        This effectively blocks access to the listed websites by redirecting them to the specified address.
        """
        
        f = open(self.path, 'w')
        for domain in self.blocked_sites:
            f.write(f'\n{self.redirect}  {domain}    #added using Supervise.')
        f.close()

    def add_website(self, domain: str):
        """
        Adds a website to the block list and updates the hosts file to reflect the change.
        
        Args:
            domain (str): The domain of the website to be added to the block list.
        
        This method appends the provided domain to the `self.blocked_sites` list, and then calls the `update_file()` method to write the updated block list to the hosts file.
        """

        self.blocked_sites.append(domain)
        self.update_file()

    def remove_website(self, domain: str):
        """
        Removes a website from the block list and updates the hosts file to reflect the change.
        
        Args:
            domain (str): The domain of the website to be removed from the block list.
        
        This method removes the provided domain from the `self.blocked_sites` list, and then calls the `update_file()` method to write the updated block list to the hosts file.
        """
        
        if domain in self.blocked_sites:
            self.blocked_sites.remove(domain)
            self.update_file()

    def extract_history(self, history_db: str) -> list[tuple]:
        """
        Extracts the browsing history from the Chrome browser's SQLite database and returns a list of tuples containing the URL, title, and last visited date/time for the 20 most recent visits.
        
        This function first closes the Chrome browser to gain access to the database file, then connects to the SQLite database and executes a SQL query to retrieve the desired history data.
        The results are then returned as a list of tuples.
        
        Args:
            history_db (str): The file path to the Chrome browser's SQLite history database.
        
        Returns:
            list of tuples: A list of tuples containing the URL, title, and last visited date/time for the 20 most recent visits.
        """
        # Close chrome in order to access its database
        os.system("taskkill /f /im chrome.exe")

        c = sqlite3.connect(history_db)
        cursor = c.cursor()
        select_statement = """SELECT
                                DISTINCT u.url AS URL, 
                                u.title AS Title, 
                                -- Convert the Unix timestamp to a human-readable date and time format
                                strftime('%m-%d-%Y %H:%M', (u.last_visit_time/1000000.0) - 11644473600, 'unixepoch', 'localtime') AS "Last Visited Date Time"
                            FROM
                                urls u,
                                visits v 
                            WHERE
                                u.id = v.url
                            ORDER BY
                                u.last_visit_time DESC -- Order by last visited time in descending order
                            LIMIT 20;
                            """
        cursor.execute(select_statement)
        results = cursor.fetchall()
        c.close()

        # Open chrome again
        os.system("start \"\" https://www.google.com")
        
        return results
        
    def build_history_string(self) -> dict[str, str]:
        """
        Builds a dictionary of the user's browsing history, where the keys are the last visited date and time concatenated with the page title, and the values are the corresponding URLs.
        
        This method first retrieves the Chrome browser's SQLite history database file path, then calls the `extract_history()` method to extract the 20 most recent browsing history entries. The resulting list of tuples is then used to construct the `browsing_history` dictionary, where the key is a string containing the last visited date and time, and the title, and the value is the corresponding URL.
        
        Returns:
            browsing_histoyry (dict[str, str]): A dictionary of the user's browsing history, where the keys are the last visited date and time concatenated with the page title, and the values are the corresponding URLs.
        """
        # Get the user directory dynamically
        user_dir = os.path.expanduser("~")
        history_db = os.path.join(user_dir, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History')

        history_data = self.extract_history(history_db)

        browsing_history = {}
        for url, title, last_visit_time in history_data:
            browsing_history[f"{last_visit_time} - {title}"] = url

        return browsing_history

class Screenshot:
    def screenshot(self) -> bytes:
        """
        Takes a screenshot, compresses it using gzip, and returns the compressed bytes.
        
        Returns:
            bytes: The compressed screenshot data.
        """
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