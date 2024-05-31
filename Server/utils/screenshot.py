import gzip
import pickle
from PIL import ImageGrab

class Screenshot:
    def screenshot(self) -> bytes:
        """
        Takes a screenshot, compresses it using gzip, and returns the compressed bytes.
        
        Returns:
            bytes: The compressed screenshot data.
        """
        pic = ImageGrab.grab()
        pic_bytes = pic.tobytes()
        compressed_pic = gzip.compress(pic_bytes)
        return pickle.dumps(compressed_pic)