import tkinter as tk
from tkinter import messagebox as mb
from app_utils import Client
from icecream import ic
import re


palette = {
    'background_color': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class ClientApp:
    def __init__(self):
        self.ip = ''
        self.login_screen()
        self.client = Client(self.ip, 8008)
        self.client.start()
        self.parental_control(self.ip) # Call the parental_control method with the retrieved IP

    def login_screen(self):
        def on_login_button_click():
            self.ip = ip_entry.get()  # Retrieve text from entry widget
            ip_regex = r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b'
            if re.match(ip_regex, self.ip):
                login.destroy()  # Close the login window
            else:
                mb.showerror(title = "IP Error", message = "Check your ip adress and try again")

        login = tk.Tk()
        login.title("Log In")
        login.geometry('700x500')
        login.attributes('-topmost', True)
        login['background'] = palette['background_color']

        ip_label = tk.Label(
            login,
            text="Children IP Address",
            font=("CoolveticaRg-Regular", 20),
            fg=palette['text_color'],
            bg=palette['background_color']
        )
        ip_entry = tk.Entry(
            login,
            width=30
        )
        login_button = tk.Button(
            login,
            text='login',
            command=on_login_button_click,
            width=15,
            font=("CoolveticaRg-Regular", 14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        logo = tk.Label(
            login,
            text="Supervise.",
            font=("CoolveticaRg-Regular", 25),
            bg=palette['background_color'],
            fg=palette['text_color']
        )

        ip_label.place(relx=0.5, rely=0.35, anchor='center')
        ip_entry.place(relx=0.5, rely=0.43, anchor='center')
        login_button.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        login.mainloop()
            
    def parental_control(self, ip):
        def on_window_close(): #TODO make it work
            parental.destroy()
            self.client.close_client()

        parental = tk.Tk()
        parental.geometry('700x500')
        parental.title("Parental Control")
        parental['background'] = palette['background_color']
        parental.protocol("WM_DELETE_WINDOW", lambda: on_window_close())

        connected_to_label = tk.Label(
            parental,
            text = f'Currently connected to {ip}',
            font=("CoolveticaRg-Regular",14),
            bg=palette['background_color'],
            fg=palette['text_color']
        )
        screenshot_button = tk.Button(
            parental,
            text='Take Screenshot',
            command=lambda: self.client.request_data(3),
            width=30,
            font=("CoolveticaRg-Regular",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        block_button = tk.Button(
            parental,
            text='Block Computer',
            command= lambda: self.client.request_data(1),
            width=30,
            font=("CoolveticaRg-Regular",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        web_blocker_button = tk.Button(
            parental,
            text='Web Blocker',
            command=lambda: self.web_blocker(parental),
            width=30,
            font=("CoolveticaRg-Regular",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        screentime_button = tk.Button(
            parental,
            text='Screentime',
            command=lambda: self.screentime(parental),
            width=30,
            font=("CoolveticaRg-Regular",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        switch_computer_button = tk.Button(
            parental,
            text='Switch Computer',
            command=lambda: self.switch_computer(parental),
            font=("CoolveticaRg-Regular",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        logo = tk.Label(
            parental,
            text="Supervise.",
            font=("CoolveticaRg-Regular",25),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        connected_to_label.place(rely=0.15,relx=0.5, anchor= 'center')
        screenshot_button.place(rely=0.3,relx=0.5, anchor= 'center')
        block_button.place(rely=0.4,relx=0.5, anchor= 'center')
        web_blocker_button.place(rely=0.5,relx=0.5, anchor= 'center')
        screentime_button.place(rely=0.6,relx=0.5, anchor= 'center')
        switch_computer_button.place(rely=0.95,relx=0.12, anchor= 'center')
        logo.place(relx = 0.5, rely = 0.9, anchor = 'center')
        
        parental.mainloop()

    def screentime(self, parental):
        screentime = tk.Toplevel(parental)
        screentime.geometry('700x500')
        screentime.title("Screen Time")
        screentime['background'] = palette['background_color']

    def web_blocker(self, parental):
        web_blocker = tk.Toplevel(parental)
        web_blocker.geometry('700x500')
        web_blocker.title("Web Blocker")
        web_blocker['background'] = palette['background_color']

    def switch_computer(self, parental):
        parental.destroy()
        self.login()

if __name__== '__main__':
    app = ClientApp()


