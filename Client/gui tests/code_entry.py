import tkinter as tk

palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}


def create_2fa_window():
    def submit_code():
        entered_code = code_entry.get()
        # You can add your code validation or processing logic here
        print(f"Submitted code: {entered_code}")

    # Create the main window
    root = tk.Tk()
    root.title("Enter your 2FA code")
    root.geometry("300x150")  # You can adjust the window size as needed

    # Apply the color palette
    root.configure(bg=palette['blue_bg'])

    # Title label
    title_label = tk.Label(root, text="Enter your 2FA code:", font=('Calibri', 20), fg=palette['text_color'], bg=palette['blue_bg'])
    title_label.pack(pady=5)

    # Entry widget for the code
    code_entry = tk.Entry(root, font=('Calibri', 14), bg=palette['text_color'], fg=palette['blue_bg'])
    code_entry.pack(pady=5)

    # Submit button
    submit_button = tk.Button(root, text="Submit", command=submit_code, font=('Calibri', 14), width=15, bg=palette['button_color'], fg=palette['text_color'], border=0)
    submit_button.pack(pady=5)

    # Start the Tkinter event loop
    root.mainloop()

create_2fa_window()