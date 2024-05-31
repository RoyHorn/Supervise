import sqlite3
from datetime import datetime, timedelta

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

            if result: # if the result is not None
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
            
            if last_log_date is not None: # if the result is not None
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
