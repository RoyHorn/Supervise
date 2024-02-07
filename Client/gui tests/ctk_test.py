import threading
import customtkinter as ctk
from ctk_settings import *
from CTkListbox import *
from tkinter import messagebox as mb
from Client.app_utils import Client
from icecream import ic
import re, time

ctk.set_appearance_mode(APPERANCE_MODE)
ctk.set_default_color_theme(COLOR_THEME)

palette = {
    'background_color': '#312F31',
    'text_color': '#E7ECEF',
    'button_color': '#2E6FA6'
}

class ClientApp:
    def __init__(self):
        self.ip = ''
        self.login_screen()

    def start_client(self):
        self.client = Client(self.ip, 8008)
        self.client.start()
        self.parental_control()

    def login_screen(self):
        def on_login_button_click():
            self.ip = ip_entry.get()
            ip_regex = r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b'
            if re.match(ip_regex, self.ip):
                login.destroy()
                self.start_client()
            else:
                mb.showerror(title="IP Error", message="Check your ip address and try again")

        login = ctk.CTk()
        login.title("Log In")
        login.geometry('700x500')
        login.attributes('-topmost', True)

        ip_label = ctk.CTkLabel(login, text="Children IP Address")
        ip_entry = ctk.CTkEntry(login)
        login_button = ctk.CTkButton(login, text='login', command=on_login_button_click)
        logo = ctk.CTkLabel(login, text="Supervise.")

        ip_label.place(relx=0.5, rely=0.35, anchor='center')
        ip_entry.place(relx=0.5, rely=0.43, anchor='center')
        login_button.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        login.mainloop()

    def on_window_close(self):
        self.parental.destroy()
        self.client.close_client()

    def parental_control(self):
        self.parental = ctk.CTk()
        self.parental.geometry('700x500')
        self.parental.title("Parental Control")
        self.parental.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close())

        connected_to_label = ctk.CTkLabel(self.parental, text=f'Currently connected to {self.ip}')
        screenshot_button = ctk.CTkButton(self.parental, text='Take Screenshot', command=lambda: self.client.request_data(3))
        block_button = ctk.CTkButton(self.parental, text='Block Computer', command=lambda: self.client.request_data(1))
        web_blocker_button = ctk.CTkButton(self.parental, text='Web Blocker', command=self.web_blocker)
        screentime_button = ctk.CTkButton(self.parental, text='Screentime', command=self.screentime)
        switch_computer_button = ctk.CTkButton(self.parental, text='Switch Computer', command=lambda: self.client.request_data(2))
        logo = ctk.CTkLabel(self.parental, text="Supervise.")

        connected_to_label.place(rely=0.15, relx=0.5, anchor='center')
        screenshot_button.place(rely=0.3, relx=0.5, anchor='center')
        block_button.place(rely=0.4, relx=0.5, anchor='center')
        web_blocker_button.place(rely=0.5, relx=0.5, anchor='center')
        screentime_button.place(rely=0.6, relx=0.5, anchor='center')
        switch_computer_button.place(rely=0.95, relx=0.12, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        self.parental.mainloop()

    def screentime(self):
        screentime = ctk.CTkToplevel(self.parental)
        screentime.geometry('700x500')
        screentime.title("Screen Time")

    def web_blocker(self):
        def on_add_button_click():
            website = website_entry.get()
            if website:
                listbox.insert("END", website)
                website_entry.delete(0, ctk.END)
                self.client.request_data(5, website)

        def on_remove_button_click():
            try:
                selected_index = listbox.curselection()
                website = listbox.get(selected_index)
                listbox.delete(selected_index)
                self.client.request_data(6, website)
            except IndexError:
                pass

        web_blocker = ctk.CTkToplevel(self.parental)
        web_blocker.geometry('700x500')
        web_blocker.title("Web Blocker")

        # Create frames
        remove_frame = ctk.CTkFrame(web_blocker)
        add_frame = ctk.CTkFrame(web_blocker)

        remove_frame.place(relx=0.3, rely=0.3, relwidth=0.3, relheight=0.5, anchor = 'center')
        add_frame.place(relx=0.7, rely=0.5, relwidth=0.3, anchor = 'center')

        listbox = CTkListbox(remove_frame)
        website_entry = ctk.CTkEntry(add_frame)
        add_button = ctk.CTkButton(add_frame, text='Add Website', command=on_add_button_click)
        remove_button = ctk.CTkButton(remove_frame, text='Remove Website', command=on_remove_button_click)

        listbox.pack(side="top", fill="both", anchor = 'center')
        remove_button.pack(side="bottom", pady=1, anchor = 'center')
        
        website_entry.pack(side="top", fill="both", anchor = 'center')
        add_button.pack(side="bottom", pady=1, anchor = 'center')

        self.client.request_data(4)
        threading.Thread(target=self.load_websites, args=(listbox,)).start()


    def load_websites(self, listbox):
        time.sleep(0.5)  # allows the current sites list to be loaded
        website_list = self.client.get_sites_list()
        if len(website_list) > 0:
            for website in website_list:
                listbox.insert("END", website)

if __name__ == '__main__':
    app = ClientApp()
