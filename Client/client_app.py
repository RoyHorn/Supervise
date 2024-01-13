import tkinter as tk
from tkinter import messagebox as mb
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from app_utils import Client
import pandas as pd
import time
import re

palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class ClientApp:
    def __init__(self):
        self.ip = ''
        self.client = None

    def run(self):
        self.login_screen()

    def login_screen(self):
        def on_login_button_click():
            self.ip = ip_entry.get()
            ip_regex = r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b'
            if re.match(ip_regex, self.ip):
                login.destroy()
                self.client = Client(self.ip, 8008)
                self.client.start()
                self.parental_control()
            else:
                mb.showerror(title="IP Error", message="Check your ip address and try again")

        login = tk.Tk()
        login.title("Log In")
        login.geometry('700x500')
        login.attributes('-topmost', True)
        login['background'] = palette['background_color']

        ip_label = tk.Label(
            login,
            text="Children IP Address",
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
            font=("Calibri", 14),
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
            
    def parental_control(self):
        '''opens after connecting to the server and holds all of the main functions of the app'''
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
            text = f'Currently connected to {self.ip}',
            font=("Calibri",14),
            bg=palette['background_color'],
            fg=palette['text_color']
        )
        screenshot_button = tk.Button(
            parental,
            text='Take Screenshot',
            command=lambda: self.client.request_data(3),
            width=30,
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        block_button = tk.Button(
            parental,
            text='Block Computer',
            command= lambda: self.client.request_data(1),
            width=30,
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        web_blocker_button = tk.Button(
            parental,
            text='Web Blocker',
            command=lambda: self.web_blocker(parental),
            width=30,
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        screentime_button = tk.Button(
            parental,
            text='Screentime',
            command=lambda: self.screentime(parental),
            width=30,
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        switch_computer_button = tk.Button(
            parental,
            text='Switch Computer',
            command=lambda: self.client.request_data(2),
            font=("Calibri",14),
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
        def on_button_click():
            if daily_limit_entry['state'] == 'disabled':
                daily_limit_entry['state'] = 'normal'
                daily_limit_button['text'] = 'Set'
            else:
                daily_limit_entry['state'] = 'disabled'
                daily_limit_button['text'] = 'Change'
                self.client.request_data(8, daily_limit_var.get())
                canvas.draw()

        '''recives data from the server about screen time from the server and shows it nicely'''
        screentime = tk.Toplevel(parental)
        screentime.geometry('700x500')
        screentime.title("Screen Time")
        screentime['background'] = palette['blue_bg']

        self.client.request_data(7)
        self.client.request_data(8)

        time.sleep(0.5)

        screentime_data = self.client.get_screentime_list()

        daily_limit_var = tk.StringVar()
        daily_limit_var.set(self.client.get_screentime_limit())

        # Create a DataFrame from the data
        df = pd.DataFrame(screentime_data, columns=['Date', 'Time'])
        # Convert the 'Date' column to datetime format
        df['Date'] = pd.to_datetime(df['Date'])
        # Format the 'Date' column to dd/mm/yy
        df['Date'] = df['Date'].dt.strftime('%d/%m/%y')
        # Create a Matplotlib figure and axis for the graph
        fig, ax = plt.subplots()

        # Plotting the bar graph
        bars = ax.bar(df['Date'], df['Time'], color=palette['blue_bg'])
        ax.set_xlabel('Date')
        ax.set_ylabel('Screen Time (hours)')

        # Hide dates without data
        ax.set_xticks(df['Date'])

        # Add weekly average line
        weekly_avg = df['Time'].mean()
        avg_line = ax.axhline(y=weekly_avg, color='red', linestyle='--', label=f'Weekly Avg: {weekly_avg:.2f} hours')
        # limit_line = ax.axhline(y=daily_limit_var.get(), color='green', linestyle='-', label=f'Daily Limit: {daily_limit_var.get():.2f} hours')

        # Add a title label
        title_label = tk.Label(screentime, text='Screen Time', font=('Helvetica', 16, 'bold'), fg='white', bg='#087CA7')

        daily_limit_label = tk.Label(screentime, text = 'Daily Limit', fg='white', bg='#087CA7')
        daily_limit_entry = tk.Entry(screentime, width=10, state='disabled', textvariable=daily_limit_var)
        daily_limit_button = tk.Button(screentime, text  = 'Change', command = on_button_click)


        # Embed the Matplotlib figure in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=screentime)
        canvas_widget = canvas.get_tk_widget()
        
        title_label.pack(pady=10)
        daily_limit_label.pack()
        daily_limit_entry.pack()
        daily_limit_button.pack()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    def web_blocker(self,parental):
        '''takes information about the blocked sites from the hosts file on server, formats it and shows it nicely -
        allows to add/remove sites from the list'''
        def on_add_button_click():
            website = website_entry.get()
            if website:  # Ensure the entry isn't empty
                listbox.insert(tk.END, website)
                website_entry.delete(0, tk.END)  # Clear the entry after adding
                self.client.request_data(5, website)

        def on_remove_button_click():
            try:
                selected_index = listbox.curselection()[0]  # Get the index of the selected item
                website = listbox.get(selected_index)
                listbox.delete(selected_index)  # Remove the selected item
                self.client.request_data(6, website)
            except IndexError:  # Handle the case where no item is selected
                pass  # Do nothing if no item is selected


        web_blocker = tk.Toplevel(parental)
        web_blocker.geometry('700x500')
        web_blocker.title("Web Blocker")
        web_blocker['background'] = palette['background_color']

        listbox = tk.Listbox(web_blocker)
        website_entry = tk.Entry(
            web_blocker,
            width=30
        )
        add_button = tk.Button(
            web_blocker,
            text='Add Website',
            command=lambda: on_add_button_click(),
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        remove_button = tk.Button(
            web_blocker,
            text='Remove Website',
            command=lambda: on_remove_button_click(),
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )

        listbox.place(relx=0.6, rely=0.3)
        website_entry.place(relx=0.2, rely=0.4)
        add_button.place(relx=0.25, rely=0.45)
        remove_button.place(relx=0.58, rely=0.65)

        self.client.request_data(4)
        time.sleep(0.5) #allows the current sites list to be loaded
        website_list = self.client.get_sites_list()
        if len(website_list)>0:
            for website in website_list:
                listbox.insert(tk.END, website)

if __name__== '__main__':
    app = ClientApp()
    app.run()
 


