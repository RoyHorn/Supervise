from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class Encryption():
    """
    The `Encryption` class provides a simple interface for encrypting and decrypting data using RSA encryption.
    
    The class generates a 1024-bit RSA key pair on initialization, and provides methods to encrypt and decrypt data using the public and private keys, respectively.
    
    The `encrypt()` method takes a key (either the public key or the private key) and some data, and returns the encrypted data.
    The `decrypt()` method takes the encrypted ciphertext and returns the original plaintext message, along with the message type and command.
    
    The `get_public_key()` method returns the public key as a PEM-encoded string
    The `recv_public_key()` method imports a public key from a PEM-encoded string.
    """
    def __init__(self):
        self.key = RSA.generate(1024)
        self.public_key = self.key.publickey()
        self.private_key = self.key

    def encrypt(self, key, data: bytes) -> bytes:
        """
        Encrypts the given data using the provided RSA key.
        
        The data is encrypted in chunks of 86 bytes to avoid exceeding the maximum plaintext size for the RSA key. The encrypted chunks are then concatenated and returned as the final encrypted data.
        
        Args:
            key (Crypto.PublicKey.RSA.RsaKey): The RSA key to use for encryption.
            data (bytes): The data to be encrypted.
        
        Returns:
            encrypted_data (bytes): The encrypted data.
        """
        cipher = PKCS1_OAEP.new(key)
        chunk_size = 86 
        encrypted_data = b""

        for i in range(0, len(data), chunk_size): # Encrypt in chunks
            chunk = data[i:i + chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_data += encrypted_chunk

        return encrypted_data
    
    def decrypt(self, ciphertext: bytes) -> tuple[str, str, str]:
        """
        Decrypts the provided ciphertext using the private RSA key.
        
        The ciphertext is decrypted in chunks of 128 bytes to avoid exceeding the maximum ciphertext size for the RSA key.
        The decrypted chunks are then concatenated and returned as the final decrypted message.
        
        The decrypted message is then split into the message type, command, and message content.
        
        Args:
            ciphertext (bytes): The encrypted ciphertext to be decrypted.
        
        Returns:
            type (str): The type of the decrypted message.
            cmmd (str): The command of the decrypted message.
            msg (str): The content of the decrypted message.
        """
        decrypt_cipher = PKCS1_OAEP.new(self.private_key)
        chunk_size = 128
        decrypted_message = b""

        for i in range(0, len(ciphertext), chunk_size): # Decrypt in chunks
            chunk = ciphertext[i:i + chunk_size]
            decrypted_chunk = decrypt_cipher.decrypt(chunk)
            decrypted_message += decrypted_chunk

        # Split the decrypted message into its components
        decrypted_message = decrypted_message.decode()
        type = decrypted_message[:1]
        cmmd = decrypted_message[1:2]
        msg = decrypted_message[2:]

        return (type, cmmd, msg)
    
    def get_public_key(self) -> bytes:
        """
        Returns the public RSA key as a byte string.
        """
        return self.public_key.export_key()
    
    def recv_public_key(self, pem_key: bytes):
        """
        Imports an RSA public key from a PEM-encoded string.
        
        Args:
            pem_key (bytes): The PEM-encoded RSA public key.
        
        Returns:
            RSA Key : The imported RSA public key object.
        """
        return RSA.import_key(pem_key)
