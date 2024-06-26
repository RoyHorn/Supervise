import tkinter as tk
import pyotp
import threading

palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class TwoFactorAuthentication(threading.Thread):
    """
    Implements a two-factor authentication (2FA) system using a Time-based One-Time Password (TOTP) algorithm.
    
    The `TwoFactorAuthentication` class generates a random secret key and uses it to create a TOTP object.
    It provides methods to generate and verify 2FA codes, as well as to display the current 2FA code in a Tkinter window.
    
    The `generate_authenication_code()` method generates the current 2FA code based on the secret key and the current time.
    The `verify_code()` method verifies a provided 2FA code against the current code generated by the TOTP object.
    The `create_code_display()` method creates a Tkinter window that continuously displays the current 2FA code.
    The `display_code()` method starts the 2FA code display window in a separate thread.
    The `stop_code_display()` method stops the 2FA code display window.
    """
    def __init__(self):
        super().__init__()
        self.secret = pyotp.random_base32() # Generate a random base32 secret key
        self.totp = pyotp.TOTP(self.secret) # Create a TOTP (Time-based One-Time Password) object using the secret key
        self.show = False # Variable to control whether to show the TOTP

    def generate_authenication_code(self) -> str:
        """
        Generates the current Time-based One-Time Password (TOTP) code based on the secret key.
        
        Returns:
            str: The current TOTP code.
        """
        return self.totp.now()

    def verify_code(self, input_code: str) -> bool:
        """
        Verifies the provided Time-based One-Time Password (TOTP) code against the current TOTP code generated by the TOTP object.
        
        Args:
            input_code (str): The TOTP code to be verified.
        
        Returns:
            bool: True if the provided code matches the current TOTP code, False otherwise.
        """
        return self.totp.verify(input_code)

    def create_code_display(self):
        """
        Creates a Tkinter window that continuously displays the current Time-based One-Time Password (TOTP) code.
        
        The `create_code_display()` method creates a Tkinter window with a label that displays the current TOTP code.
        The window is set to be always on top, and the window's close button is configured to call the `stop_code_display()` method to stop the code display.
        
        The method enters a loop that updates the code label with the current TOTP code generated by the `generate_authenication_code()` method. The loop continues as long as the `show` flag is set to `True`.
        """
        self.show = True
        window = tk.Tk()
        window.title('Code Screen')
        window.configure
        window.wm_attributes("-topmost", True)
        window.protocol("WM_DELETE_WINDOW", lambda: self.stop_code_display())
        window['background'] = palette['blue_bg']

        frame = tk.Frame(window, bg=palette['blue_bg'])
        frame.pack(pady=10)

        # Create a label to display the code
        label = tk.Label(frame, text=f"Two Factor Authenication Code:", font=("Calibri", 20), fg=palette['text_color'], bg=palette['blue_bg'], padx=20)
        code_label = tk.Label(frame, text=f"", font=("Calibri", 50), fg=palette['text_color'], bg=palette['blue_bg'], padx=20)
        label.pack()
        code_label.pack()

        while self.show: # Loop to update the code label with the current TOTP code
            code_label.config(text=self.generate_authenication_code())
            window.update()
            window.update_idletasks()

    def display_code(self):
        """
        Displays the current Time-based One-Time Password (TOTP) code in a Tkinter window.
        """
        if not self.show: # Only create a new window if the current window is not already showing
            window_thread = threading.Thread(target=self.create_code_display)
            window_thread.start()

    def stop_code_display(self):
        """
        Stops the continuous display of the current Time-based One-Time Password (TOTP) code in the Tkinter window.
        
        This method sets the `show` flag to `False`, which causes the loop in the `create_code_display()` method to exit, effectively stopping the code display.
        """
        if self.show: # Only stop the current window if it is already showing
            self.show = False
