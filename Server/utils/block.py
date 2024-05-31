
import tkinter as tk
import threading
import datetime as dt
import keyboard

palette = {
    'background_color': '#1A1A1A',
    'blue_bg': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class Block(threading.Thread):
    """
    Responsible for blocking the computer when needed. This class manages the state of the computer block, including setting up a full-screen window with a message informing the user that their time limit has been reached, and disabling/enabling the keyboard.
    
    The `Block` class is a subclass of `Thread`, which allows it to run in a separate thread from the main application. This ensures that the blocking functionality does not block the main application.
    
    The class has the following methods:
    
    - `__init__()`: Initializes the block state, end block flag, and a lock for thread-safe access.
    - `run()`: Starts the block by disabling the keyboard, setting up the block window, and enabling the keyboard.
    - `end_block()`: Ends the block by setting the end block flag and resetting the block state.
    - `setup_window()`: Sets up the full-screen block window with a message and logo.
    - `calculate_ms_delta()`: Calculates the number of milliseconds until the next day, so that the block can be automatically released.
    - `disable_keyboard()`: Disables the keyboard by blocking all keys.
    - `enable_keyboard()`: Enables the keyboard by unblocking all keys.
    - `get_block_state()`: Returns the current block state.
    """

    def __init__(self):
        super().__init__()
        self.block_state = False
        self.end_block_flag = False
        self.block_lock = threading.Lock()

    def run(self):
        """
        Starts the block by disabling the keyboard, and setting up the block window.
        """
        self.end_block_flag = False # Reset the end block flag
        self.block_state = True # Set the block state to True
        self.disable_keyboard()
        self.setup_window()
        self.enable_keyboard() 

    def end_block(self):
        """
        Ends the block when requested by the client. This method sets the `end_block_flag` to `True` and the `block_state` to `False`, allowing the block to be released. 
        The method uses a lock to ensure thread-safe access to the block state.
        """
        with self.block_lock:
            self.end_block_flag = True # Set the end block flag
            self.block_state = False # Set the block state to False

    def setup_window(self):
        """
        Sets up the full-screen block window with a message and logo. This method is responsible for creating the Tkinter window, setting its attributes, and placing the message and logo labels on the window. The window is kept on top of other windows and cannot be closed by the user.
        
        The window is set to automatically destroy itself after the calculated number of milliseconds until the next day, using the `self.calculate_ms_delta()` method.
        
        This method runs in a loop, updating the window until the `self.end_block_flag` is set to `True`, indicating that the block should be ended.
        """
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.title("block")
        self.root['background'] = palette['blue_bg']

        # keeps the self.root on top
        self.root.wm_attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        logo = tk.Label(
            self.root,
            text="Supervise.",
            font=("CoolveticaRg-Regular", 25),
            bg=palette['blue_bg'],
            fg=palette['text_color']
        )

        message = tk.Label(
            self.root,
            text="Buddy, you have reached your time limit...",
            font=("CoolveticaRg-Regular", 60),
            bg=palette['blue_bg'],
            fg=palette['text_color']
        )

        limit = tk.Label(
            self.root,
            text="You can access your computer back tomorrow",
            font=("CoolveticaRg-Regular", 30),
            bg=palette['blue_bg'],
            fg=palette['text_color']
        )

        message.place(relx=0.5, rely=0.45, anchor='center')
        limit.place(relx=0.5, rely=0.55, anchor='center')
        logo.place(relx=0.5, rely=0.9, anchor='center')

        self.root.after(self.calculate_ms_delta(), self.root.destroy)

        while not self.end_block_flag: # Run in a loop until the end block flag is set to True
            self.root.update()
            self.root.update_idletasks()

    def calculate_ms_delta(self) -> int:
        """
        Calculates the number of milliseconds until the next day, in order to automatically release the block when the next day arrives.
        
        Returns:
            int: The number of milliseconds until the next day.
        """

        # Get the current time and date
        now = dt.datetime.now()
        tomorrow = (now + dt.timedelta(1)).replace(hour=0, minute=0, second=0)

        # Calculate the number of seconds until the next day
        delta = (tomorrow-now).seconds
        
        return delta*1000

    def disable_keyboard(self):
        """
        Disables the keyboard by blocking all keys.
        
        This function iterates through the range of key codes (0-149) and blocks each key using the `keyboard.block_key()` function. This effectively disables the entire keyboard, preventing the user from interacting with the system.
        """
        for i in range(150):
            keyboard.block_key(i)
        
    def enable_keyboard(self):
        """
        Enables the keyboard by unblocking all keys that were previously blocked.
        
        This function iterates through the range of key codes (0-149) and unblocks each key using the `keyboard.unblock_key()` function. This effectively re-enables the entire keyboard, allowing the user to interact with the system.
        """
        for i in range(150):
            keyboard.unblock_key(i)

    def get_block_state(self) -> bool:
        """
        Returns the current block state.
        """
        return self.block_state
