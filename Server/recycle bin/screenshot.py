from PIL import ImageGrab

class Screenshot:
    def screenshot(self):
        pic = ImageGrab.grab()
        return pic.tobytes()