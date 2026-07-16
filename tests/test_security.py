"""Tests for the security module: Fernet encryption and decryption."""

from app.core.security import encrypt_data, decrypt_data


class TestEncryption:
    """Test Fernet AES-256 symmetric encryption."""

    def test_encrypt_returns_string(self):
        encrypted = encrypt_data("my_secret_password")
        assert isinstance(encrypted, str)
        assert encrypted != "my_secret_password"

    def test_decrypt_recovers_original(self):
        original = "ssh_private_key_content_here"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert decrypted == original

    def test_encrypt_different_each_time(self):
        """Fernet uses a timestamp + random IV, so encryptions differ."""
        e1 = encrypt_data("same_data")
        e2 = encrypt_data("same_data")
        assert e1 != e2

    def test_roundtrip_special_characters(self):
        """Ensure special characters survive encryption round-trip."""
        data = "p@$$w0rd!#%^&*()\n\ttabs and newlines"
        assert decrypt_data(encrypt_data(data)) == data

    def test_roundtrip_unicode(self):
        data = "p@ssw0rd"
        assert decrypt_data(encrypt_data(data)) == data

    def test_roundtrip_ssh_key(self):
        """Simulate encrypting a multi-line SSH private key."""
        ssh_key = (
            "-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAA\n"
            "AAAAHHNzaC1yc2EAAAADAQABAAABgQC7...\n"
            "-----END OPENSSH PRIVATE KEY-----"
        )
        assert decrypt_data(encrypt_data(ssh_key)) == ssh_key
