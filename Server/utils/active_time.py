from threading import Thread
from datetime import datetime
import time
from utils.database import Database
from win32api import GetLastInputInfo

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
        last_input = GetLastInputInfo() #last input time
        last_active = time.time()

        while True:
            time.sleep(1)
            if GetLastInputInfo() == last_input: # User is active
                not_active_delta = time.time()-last_active
                if not_active_delta > self.STATE_CHANGE_DELAY: # If user is inactive for more than `self.STATE_CHANGE_DELAY` seconds
                    self.is_active = False
            else: # User is inactive
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
