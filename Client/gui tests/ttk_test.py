import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox as mb
from Client.app_utils import Client
import time
import re

THEME = 'darkly'

class ClientApp:
    def __init__(self):
        self.ip = ''
        self.client = None

    def run(self):
        self.login_screen()

    def login_screen(self):
        def on_login_button_click():
            ip_regex = r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b'
            if re.match(ip_regex, self.ip.get()):
                login.destroy()
                self.client = Client(self.ip.get(), 8008)
                self.client.start()
                self.parental_control()
            else:
                mb.showerror(title="IP Error", message="Check your ip address and try again")

        login = ttk.Window(themename=THEME)
        login.title("Log In")
        login.geometry('700x500')
        login.attributes('-topmost', True)

        self.ip = tk.StringVar()
        login.bind('<Return>', lambda event: on_login_button_click()) #TODO fix error

        ip_label = ttk.Label(
            login,
            text="Children IP Address"
        )
        ip_entry = ttk.Entry(
            login,
            width=30,
            textvariable= self.ip
        )
        login_button = ttk.Button(
            login,
            text='login',
            command=on_login_button_click,
            width=15
        )
        logo = ttk.Label(
            login,
            text="Supervise.",
            font="CoolveticaRg-Regular 25"
        )

        ip_label.place(relx=0.5, rely=0.35, anchor='center')
        ip_entry.place(relx=0.5, rely=0.43, anchor='center')
        login_button.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        login.mainloop()

    def parental_control(self):
        def on_window_close():
            parental.destroy()
            self.client.close_client()

        parental = ttk.Window(themename=THEME)
        parental.geometry('700x500')
        parental.title("Parental Control")
        parental.protocol("WM_DELETE_WINDOW", lambda: on_window_close())

        connected_to_label = ttk.Label(
            parental,
            text=f'Currently connected to {self.ip.get()}'
        )
        screenshot_button = ttk.Button(
            parental,
            text='Take Screenshot',
            command=lambda: self.client.request_data(3),
            width=30
        )
        block_button = ttk.Button(
            parental,
            text='Block Computer',
            command=lambda: self.client.request_data(1),
            width=30
        )
        web_blocker_button = ttk.Button(
            parental,
            text='Web Blocker',
            command=lambda: self.web_blocker(parental),
            width=30
        )
        screentime_button = ttk.Button(
            parental,
            text='Screentime',
            command=lambda: self.screentime(parental),
            width=30
        )
        switch_computer_button = ttk.Button(
            parental,
            text='Switch Computer',
            command=lambda: self.client.request_data(2)
        )
        logo = ttk.Label(
            parental,
            text="Supervise.",
            font="CoolveticaRg-Regular 25"
        )

        connected_to_label.place(rely=0.15, relx=0.5, anchor='center')
        screenshot_button.place(rely=0.3, relx=0.5, anchor='center')
        block_button.place(rely=0.4, relx=0.5, anchor='center')
        web_blocker_button.place(rely=0.5, relx=0.5, anchor='center')
        screentime_button.place(rely=0.6, relx=0.5, anchor='center')
        switch_computer_button.place(rely=0.95, relx=0.12, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        parental.mainloop()

    def screentime(self, parental):
        screentime = tk.Toplevel(parental)
        screentime.geometry('700x500')
        screentime.title("Screen Time")

    def web_blocker(self, parental):
        def on_add_button_click():
            if website_entry.get():
                listbox.insert(tk.END, website_entry.get())
                website_entry.delete(0, tk.END)
                self.client.request_data(5, website)

        def on_remove_button_click():
            try:
                selected_index = listbox.curselection()[0]
                website = listbox.get(selected_index)
                listbox.delete(selected_index)
                self.client.request_data(6, website)
            except IndexError:
                pass

        web_blocker = tk.Toplevel(parental)
        web_blocker.geometry('700x500')
        web_blocker.title("Web Blocker")
        entry_text = tk.StringVar()

        add_frame = ttk.Frame(web_blocker)
        remove_frame = ttk.Frame(web_blocker)

        listbox = tk.Listbox(web_blocker)
        remove_button = ttk.Button(
            web_blocker,
            text='Remove Website',
            command=lambda: on_remove_button_click()
        )

        website_entry = ttk.Entry(
            web_blocker,
            width=30,
            textvariable= entry_text
        )
        add_button = ttk.Button(
            web_blocker,
            text='Add Website',
            command=lambda: on_add_button_click()
        )

        website_entry.pack(pady=10)
        add_button.pack()

        listbox.pack(pady=10)
        remove_button.pack()

        add_frame.pack(side='left')
        remove_frame.pack(side='left')

        self.client.request_data(4)
        time.sleep(0.5)
        website_list = self.client.get_sites_list()
        if len(website_list) > 0:
            for website in website_list:
                listbox.insert(tk.END, website)

if __name__ == '__main__':
    app = ClientApp()
    app.run()
