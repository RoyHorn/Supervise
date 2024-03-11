import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

#color paletee
palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

# Function to update the graph with new data
def update_graph(screentime_data, time_limit):
    # Create a DataFrame from the data
    df = pd.DataFrame(screentime_data, columns=['Date', 'Time'])
    # Convert the 'Date' column to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    # Format the 'Date' column to dd/mm/yy
    df['Date'] = df['Date'].dt.strftime('%d/%m/%y')
    
    ax.clear()
    # Plotting the bar graph
    bars = ax.bar(df['Date'], df['Time'], color=palette['blue_bg'])
    ax.set_xlabel('Date')
    ax.set_ylabel('Screen Time (hours)')
    # Hide dates without data
    ax.set_xticks(df['Date'])

    # Add weekly average line
    weekly_avg = df['Time'].mean()
    avg_line = ax.axhline(y=weekly_avg, color='red', linestyle='--', label=f'Weekly Avg: {weekly_avg:.2f} hours')
    limit_line = ax.axhline(y=0.0, color='green', linestyle='-', label=f'Daily Limit: {float(time_limit):.2f} hours')

    # Add a title label
    title_label.config(text='Screen Time')

    # Embed the Matplotlib figure in the Tkinter window
    canvas.draw()

# Function to simulate receiving data
def receive_data():
    while True:
        time.sleep(5)
        # Simulating receiving data
        screentime_data = {'Date': pd.date_range(pd.Timestamp.now(), periods=5), 'Time': [i*2 for i in range(5)]}
        time_limit = 8  # Simulated daily limit
        update_graph(screentime_data, time_limit)
        time.sleep(5)  # Simulated delay for receiving data

# Create the Tkinter window
screentime = tk.Tk()
screentime.title("Screen Time Visualization")

# Create a Matplotlib figure and axis for the graph
fig, ax = plt.subplots()

# Add a title label
title_label = tk.Label(screentime, text='Screen Time', font=('Helvetica', 16, 'bold'), fg='white', bg='#087CA7')

# Embed the Matplotlib figure in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=screentime)
canvas_widget = canvas.get_tk_widget()

title_label.pack(pady=10)
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Start a thread to simulate receiving data
update_thread = threading.Thread(target=receive_data)
update_thread.daemon = True
update_thread.start()

# Start the Tkinter event loop
screentime.mainloop()
