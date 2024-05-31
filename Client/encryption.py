from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

class Encryption():
    def __init__(self):
        self.key = RSA.generate(1024)
        self.public_key = self.key.publickey()
        self.private_key = self.key

    def encrypt(self, key, data) -> bytes:
        """
        Encrypts the given data with the provided key.
        
        Args:
            key: The encryption key to use.
            data: The data to encrypt.
            
        Returns:
            The encrypted data.
        """
        cipher = PKCS1_OAEP.new(key) # Create a new cipher object
        chunk_size = 128 
        encrypted_data = b""

        for i in range(0, len(data), chunk_size): # Encrypt data in chunks
            chunk = data[i:i + chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_data += encrypted_chunk

        return encrypted_data
        
    def decrypt(self, ciphertext) -> tuple[str, str, bytes]:
        """
        Decrypts the given ciphertext using the private key.
        
        Args:
            ciphertext: The ciphertext to decrypt.
        
        Returns:
            The decrypted plaintext.
        """
        decrypt_cipher = PKCS1_OAEP.new(self.private_key)
        chunk_size = 128 
        decrypted_message = b""

        for i in range(0, len(ciphertext), chunk_size): # Decrypt data in chunks
            chunk = ciphertext[i:i + chunk_size]
            decrypted_chunk = decrypt_cipher.decrypt(chunk)
            decrypted_message += decrypted_chunk

        # Split message into type, command and data
        type = decrypted_message[:1].decode()
        cmmd = decrypted_message[1:2].decode()
        data = decrypted_message[2:]

        return type, cmmd, data
    
    def get_public_key(self):
        return self.public_key.export_key()
    
    def recv_public_key(self, pem_key):
        return RSA.import_key(pem_key)
