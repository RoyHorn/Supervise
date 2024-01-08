import time
import threading

class Hello:
    def __init__(self):
        self.list = []
        self.lock = threading.Lock()

    def run(self):
        while True:
            time.sleep(1)
            with self.lock:
                print(self.list)

    def append_to_list(self, item):
        with self.lock:
            self.list.append(item)

# Create an instance of the Hello class
a = Hello()

# Start the run method in a separate thread
thread = threading.Thread(target=a.run)
thread.start()

# Append items to the list while the loop is running
a.append_to_list('hey')
time.sleep(2)  # Sleep for 2 seconds to see the output
a.append_to_list('1')
a.append_to_list('2')
a.append_to_list('3')

# Optionally, you can join the thread to wait for it to finish
# thread.join()
