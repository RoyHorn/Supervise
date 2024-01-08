import threading, time

global active_time
active_time = 0

def count_time():
    global active_time
    
    while True:
        time.sleep(5)
        active_time += 5

def print_1():
    while True:
        print(active_time)
        time.sleep(5)

x = threading.Thread(target=count_time)
x.start()

y = threading.Thread(target=print_1)
y.start()