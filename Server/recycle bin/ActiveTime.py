from threading import Thread
import time
from win32api import GetLastInputInfo

class ActiveTime(Thread):

    def __init__(self):
        super().__init__()
        self.active_time = 0
        self.is_active = False
        self.state_change_delay = 10

    def update_is_active(self):
        '''updates the is_active argument of the class according to the active state of the computer, updates every second'''
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
        is_active_thread = Thread(target=self.update_is_active)
        count_time_thread = Thread(target=self.count_active_time)

        is_active_thread.start()
        count_time_thread.start()

        is_active_thread.join()
        count_time_thread.join()

    def reset_active_time(self):
        self.active_time = 0

    def get_active_time(self):
        return self.active_time

    def __str__(self):
        return f'active time: {self.active_time} \nis active: {self.is_active}'