# from config import palette
import tkinter as tk
from datetime import datetime
import datetime as dt
import keyboard

palette = {
    'background_color': '#087CA7',
    'text_color': '#E7ECEF',
    'button_color': '#096D92'
}

class Block:
    def start(self):
        self.root = tk.Tk()
        self.disable_keyboard()
        self.setup_window()
        self.enable_keyboard() 

    def end(self):
        pass

    def setup_window(self):
        #self.root setup
        self.root.attributes('-fullscreen', True)
        self.root.title("block")
        self.root['background'] = palette['background_color']

        #keeps the self.root on top
        self.root.wm_attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        logo = tk.Label(
            self.root,
            text="Supervise.",
            font=("CoolveticaRg-Regular",25),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        message = tk.Label(
            self.root,
            text="Buddy, you have reached your limit...",
            font=("CoolveticaRg-Regular",60),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        limit = tk.Label(
            self.root,
            text=f"You can access your computer back tomorrow",
            font=("CoolveticaRg-Regular",30),
            bg= palette['background_color'],
            fg= palette['text_color']
        )

        message.place(relx = 0.5, rely = 0.45, anchor = 'center')
        limit.place(relx = 0.5, rely = 0.55, anchor = 'center')    
        logo.place(relx = 0.5, rely = 0.9, anchor = 'center')

        self.root.after(self.calculate_ms_delta(), self.root.destroy)
        self.root.mainloop()

    def calculate_ms_delta(self):
        now = datetime.now()
        tomorrow = (now + dt.timedelta(1)).replace(hour=0, minute=0, second=0)

        delta = (tomorrow-now).seconds
        
        return delta*1000

    def disable_keyboard(self):
        for i in range(150):
            keyboard.block_key(i)
        
    def enable_keyboard(self):
        for i in range(150):
            keyboard.unblock_key(i)

obj = Block().start()