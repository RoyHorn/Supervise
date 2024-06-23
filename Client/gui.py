import matplotlib.pyplot as plt
import pandas as pd
import re
import tkinter as tk
from tkinter import messagebox as mb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from client import Client
import os
import configparser

palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class Gui:
    def __init__(self):
        self.ip = ''
        self.client = None

    def run(self):
        """Runs the client app.
            
            checks if the user selected to reconnect automatically to the last connected server, if so, it will try to connect to the last connected server.
            else, it will show the login screen.
        """
        config = configparser.ConfigParser()
        if not os.path.isfile('config.ini'):
            with open('config.ini', 'w') as configfile:
                configfile.write('[connection]\nlast_connected_ip=\nreconnect_automatically=False\n')
        config.read('config.ini')

        if config.getboolean('connection', 'reconnect_automatically'): # If the user selected to reconnect automatically to the last connected server
            self.ip = config.get('connection', 'last_connected_ip')
            self.login_protocol()
        else:
            self.login_screen()

    def login_protocol(self):
        """Handles the login protocol for the client.
        
            checks wether the connection was successful and if the client needs to be authorized and acts acordingly.
        """
        self.client = Client(self.ip, 8008)
        self.client.start()

        while self.client.auth_needed == -1 or self.client.connection_succesful == -1: # Wait for the server to respond
            if self.client.connection_succesful == 0: # If the connection was unsuccesful
                mb.showerror(title="Connection unsuccesful", message="Make sure that your kids computer is turned on and try again")
                self.login_screen()
                self.client = ''
                return
        else:
            if self.client.auth_needed == 1: # If the client needs to be authorized
                self.create_2fa_window()
            else:
                self.parental_control()

    def login_screen(self):
        """Displays the login screen GUI and handles user login.
        
        This function shows the login screen, gets the IP address from the
        user, attempts to connect to that IP, and handles any errors. It
        does not return until a successful connection is made.
        """
        def on_login_button_click():
            self.ip = ip_entry.get()
            ip_regex = r'\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b'
            if re.match(ip_regex, self.ip):
                login.destroy()

                # Write the last connected ip to the file
                config = configparser.ConfigParser()
                if not os.path.isfile('config.ini'):
                    with open('config.ini', 'w') as configfile:
                        configfile.write('[connection]\nlast_connected_ip=\nreconnect_automatically=False\n')
                config.read('config.ini')
                config.set('connection', 'last_connected_ip', self.ip)
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)

                self.login_protocol()
            else:
                mb.showerror(title="IP Error", message="Check your ip address and try again")

        def on_checkbox_toggle():
            config = configparser.ConfigParser()
            if not os.path.isfile('config.ini'):
                with open('config.ini', 'w') as configfile:
                    configfile.write('[connection]\nlast_connected_ip=\nreconnect_automatically=False\n')
            config.read('config.ini')

            if reconnect_checkbox_var.get(): # If the reconnect checkbox is checked
                config.set('connection','reconnect_automatically', 'True') # Set the reconnect automatically field in the config file to true
            else:
                config.set('connection','reconnect_automatically', 'False') # Set the reconnect automatically field in the config file to false
            with open('config.ini', 'w') as configfile:
                config.write(configfile) # Write the changes to the config file

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
        reconnect_checkbox_var = tk.BooleanVar()
        reconnect_checkbox = tk.Checkbutton(login,
                                            text="Reconnect Automatically",
                                            variable=reconnect_checkbox_var,
                                            command=on_checkbox_toggle,
                                            background=palette['background_color'],
                                            foreground=palette['text_color'],
                                            selectcolor=palette['blue_bg'])
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
        reconnect_checkbox.place(relx=0.5, rely=0.48, anchor='center')
        login_button.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        login.mainloop()
            
    def parental_control(self):
        """parental_control handles the parental control interface after successful login.
        
        This shows the parental control UI and handles related logic.
        """

        def on_window_close():
            parental.destroy()
            self.client.close_client()

        def on_block_button_click():
            """
            Handles the click event for the block button in the parental control interface.
            
            If the button text is "Start Block", it sends a request to the client to request data with the value 1 (Meaning start block).
            Otherwise, it sends a request to the client to request data with the value 2 (Meaning end block).
            """
            if block_button['text'] == "Start Block":
                self.client.request_data(1)
            else:
                self.client.request_data(2)

        def on_switch_button_click():
            """
            Handles the switching from the one computer to another.
            
            This function destroys the parental control window and resets the client object,
            then calls the login_screen method to display the login interface.
            """
            parental.destroy()
            self.client = ''
            self.login_screen()
            
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
            text='Start Block',
            command= lambda: on_block_button_click(),
            width=30,
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        self.client.set_block_button(block_button)

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
            command= on_switch_button_click,
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

    def create_2fa_window(self):
        """
        Creates and displays the 2FA authentication window.
        """

        def submit_code():
            entered_code = str(code_entry.get())
            if entered_code:
                self.client.request_data(1 ,data=entered_code ,type='a') # Sends the entered to the server for check
                root.destroy()
                while self.client.auth_succeded == -1: # Wait for the server to respond
                    pass
                else:
                    if self.client.auth_succeded == 1: # If the code is correct
                        self.parental_control()
                    else: # If the code is incorrect
                        mb.showerror("Error", "Invalid code, try again.")
                        self.login_screen()
                        self.client.close_client()
                        self.client = ''
                        self.client.auth_needed = -1
                        self.client.auth_succeded = -1

        # Create the main window
        root = tk.Tk()
        root.title("2FA Authorizer")
        root.geometry("300x150")  # You can adjust the window size as needed

        # Apply the color palette
        root.configure(bg=palette['blue_bg'])

        # Title label
        title_label = tk.Label(root, text="Enter your 2FA code:", font=('Calibri', 20), fg=palette['text_color'], bg=palette['blue_bg'])
        title_label.pack(pady=5)

        # Entry widget for the code
        code_entry = tk.Entry(root, font=('Calibri', 14), bg=palette['text_color'])
        code_entry.pack(pady=5)

        # Submit button
        submit_button = tk.Button(root, text="Submit", command=submit_code, font=('Calibri', 14), width=15, bg=palette['button_color'], fg=palette['text_color'], border=0)
        submit_button.pack(pady=5)

        # Start the Tkinter event loop
        root.mainloop()

    def screentime(self, parental):
        """Displays the screentime screen.
        
        Parameters:
            parental (tk.Tk): The parental control window object.
        """

        def on_button_click():
            """
            Toggles the state of the daily limit entry field and updates the button text accordingly.
            If the entry field is disabled, it is enabled and the button text is set to "Set".
            If the entry field is enabled, it is disabled and the button text is set to "Change".
            The current value of the entry field is then inserted into the field and the client is notified of the new daily limit.
            """
            if daily_limit_entry['state'] == 'disabled':
                daily_limit_entry['state'] = 'normal'
                daily_limit_button['text'] = 'Set'
            else:
                daily_limit_entry['state'] = 'disabled'
                daily_limit_button['text'] = 'Change'
                daily_limit_entry.insert(0, daily_limit_entry.get())
                self.client.request_data(9, daily_limit_entry.get())
                update_limitline(float(daily_limit_entry.get()))  # Update the y-data of the limit line

        def update_data(screentime_data: list, time_limit: str):
            """
            Updates the data visualization for the screentime data.
            
            Parameters:
                screentime_data (list): A list of tuples containing the date and screen time data.
                time_limit (str): The daily screen time limit set by the user.
            
            This function creates a DataFrame from the provided screentime data, formats the date column, and plots a bar graph of the screen time data. It also adds a weekly average line and a daily limit line to the plot. The updated plot is then drawn on the canvas.
            """
            # Create a DataFrame from the data
            df = pd.DataFrame(screentime_data, columns=['Date', 'Time'])
            # Convert the 'Date' column to datetime format
            df['Date'] = pd.to_datetime(df['Date'])
            # Format the 'Date' column to dd/mm/yy
            df['Date'] = df['Date'].dt.strftime('%d/%m/%y')

            # Plotting the bar graph
            bars = ax.bar(df['Date'], df['Time'], color=palette['blue_bg'])
            ax.set_xlabel('Date')
            ax.set_ylabel('Screen Time (hours)')

            # Hide dates without data
            ax.set_xticks(df['Date'])

            # Add weekly average line
            weekly_avg = df['Time'].mean()
            avg_line = ax.axhline(y=weekly_avg, color='red', linestyle='--', label=f'Weekly Avg: {weekly_avg:.2f} hours')
            global limit_line
            limit_line = ax.axhline(y=float(time_limit), color='green', linestyle='-', label=f'Daily Limit: {float(time_limit):2f} hours')

            canvas.draw()

        def update_limitline(new_limit):
            global limit_line
            limit_line.set_ydata(float(new_limit))  # Update the y-data of the limit line
            canvas.draw()

        '''recives data from the server about screen time from the server and shows it nicely'''
        screentime = tk.Toplevel(parental)
        screentime.geometry('700x500')
        screentime.title("Screen Time")
        screentime['background'] = palette['blue_bg']

        # Add a title label
        title_label = tk.Label(screentime, text='Screen Time', font=('Helvetica', 16, 'bold'), fg='white', bg='#087CA7')

        daily_limit_label = tk.Label(screentime, text = 'Daily Limit', fg='white', bg='#087CA7')
        daily_limit_entry = tk.Entry(screentime, width=10)
        daily_limit_entry.config(state='disabled')
        daily_limit_button = tk.Button(screentime, text  = 'Change', command = on_button_click)

        fig, ax = plt.subplots()
        limit_line = None

        # Embed the Matplotlib figure in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=screentime)
        canvas_widget = canvas.get_tk_widget()
        
        title_label.pack(pady=10)
        daily_limit_label.pack()
        daily_limit_entry.pack()
        daily_limit_button.pack()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.client.request_data(7)
        self.client.request_data(8)

        while True:
            screentime.update()
            screentime.update_idletasks()

            if self.client.get_screentime_limit() != -1 and self.client.get_screentime_list() != -1: # If the data was recived 
                screentime_data = self.client.get_screentime_list()
                time_limit = self.client.get_screentime_limit()

                update_data(screentime_data, time_limit)

                daily_limit_entry.config(state='normal')
                daily_limit_entry.insert(0, time_limit)
                daily_limit_entry.config(state='disabled')

                self.client.screentime_list = -1 # Reset the data for the next time
                self.client.screentime_limit = -1 # Reset the data for the next time
    
    def web_blocker(self,parental):
        '''web_blocker: Displays the web blocking GUI to allow parents to block websites.
        
        Parameters:
            parental (tk.Tk): The main parental control Tkinter window.
        
        Returns:
            None
        '''

        def on_add_button_click():
            website = website_entry.get()
            if website:  # Ensure the entry isn't empty
                website_listbox.insert(tk.END, website)
                website_entry.delete(0, tk.END)  # Clear the entry after adding
                self.client.request_data(5, website) # Send the website to the server
            else: # Handle the case where the entry is empty
                try: # Try to get the selected item from the listbox
                    selected_index = history_listbox.curselection()[0]
                    website = browsing_history[history_listbox.get(selected_index)]
                except:
                    pass

                if website: 
                    website_listbox.insert(tk.END, website) 
                    self.client.request_data(5, website) # Send the website to the server

        def on_remove_button_click():
            try:
                selected_index = website_listbox.curselection()[0]  # Get the index of the selected item
                website = website_listbox.get(selected_index)
                website_listbox.delete(selected_index)  # Remove the selected item
                self.client.request_data(6, website)
            except IndexError:  # Handle the case where no item is selected
                pass  # Do nothing if no item is selected
        
        def on_browsing_history_listbox_click(event):
            try:
                selected_index = history_listbox.curselection()[0]  # Get the index of the selected item
                website = browsing_history[history_listbox.get(selected_index)]
                os.system(f"start \"\" {website}")
            except IndexError:  # Handle the case where no item is selected
                pass  # Do nothing if no item is selected

        web_blocker = tk.Toplevel(parental)
        web_blocker.resizable(False, False) 
        web_blocker.geometry('700x500')
        web_blocker.title("Web Blocker")
        web_blocker['background'] = palette['background_color']

        tutorial_label = tk.Label(
            web_blocker,
            text= 'ENTER URL IN THIS FORMAT: "http://www.example.com"',
            font=("Calibri",20),
            bg=palette['background_color'],
            fg=palette['text_color']
        )
        history_listbox = tk.Listbox(web_blocker, width=60, height=14)
        history_listbox.bind("<Double-Button>", on_browsing_history_listbox_click)
        website_listbox = tk.Listbox(web_blocker, width=22)
        website_entry = tk.Entry(
            web_blocker,
            width=22
        )
        add_button = tk.Button(
            web_blocker,
            text=' Add ',
            command=lambda: on_add_button_click(),
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )
        remove_button = tk.Button(
            web_blocker,
            text=' Remove ',
            command=lambda: on_remove_button_click(),
            font=("Calibri",14),
            bg=palette['button_color'],
            fg=palette['text_color'],
            border=0
        )

        tutorial_label.place(relx=0.05, rely=0.1)
        history_listbox.place(relx=0.35, rely=0.2)
        website_listbox.place(relx=0.1, rely=0.2)
        website_entry.place(relx=0.1, rely=0.55)
        add_button.place(relx=0.1, rely=0.61)
        remove_button.place(relx=0.175, rely=0.61)
        

        self.client.request_data(4) # Request the browsing history and blocked sites list

        while True:
            web_blocker.update()
            web_blocker.update_idletasks()

            if self.client.blocked_sites != -1 and self.client.browsing_history != -1: # Check if the data has been updated
                website_list = self.client.blocked_sites
                browsing_history = self.client.browsing_history

                self.client.blocked_sites = -1 # Reset the data for the next time
                self.client.browsing_history = -1 # Reset the data for the next time

                if len(website_list)>0: # Add the blocked websites to the blocked sites listbox
                    for website in website_list:
                        website_listbox.insert(tk.END, website)
                if len(browsing_history)>0: # Add the browsing history to the history listbox
                    for site in browsing_history.keys():
                        history_listbox.insert(tk.END, site)

if __name__== '__main__':
    app = Gui()
    app.run()

 


