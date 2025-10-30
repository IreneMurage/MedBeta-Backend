from cryptography.fernet import Fernet
from flask import current_app

def encrypt_text(plain_text: str) -> str:
    """Encrypt plain text using Fernet AES encryption."""
    if not plain_text:
        return None
    key = current_app.config["ENCRYPTION_KEY"].encode()
    fernet = Fernet(key)
    return fernet.encrypt(plain_text.encode()).decode()

def decrypt_text(cipher_text: str) -> str:
    """Decrypt encrypted text using Fernet AES decryption."""
    if not cipher_text:
        return None
    key = current_app.config["ENCRYPTION_KEY"].encode()
    fernet = Fernet(key)
    return fernet.decrypt(cipher_text.encode()).decode()
