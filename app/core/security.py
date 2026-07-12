from cryptography.fernet import Fernet
from app.core.config import settings

# Initialize symmetric Fernet encryption with key from config
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data (e.g. passwords, SSH keys) using AES-128/256.
    Returns a URL-safe base64-encoded string.
    """
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt base64-encoded cipher text back into plain text.
    """
    return fernet.decrypt(encrypted_data.encode()).decode()
