"""Tests for the auth service: password hashing, JWT tokens, and verification."""

import pytest
from datetime import timedelta

from app.modules.auth.service import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.config import settings
import jwt


class TestPasswordHashing:
    """Test bcrypt password hashing and verification."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("mysecurepassword")
        assert isinstance(hashed, str)
        assert hashed != "mysecurepassword"

    def test_hash_password_different_each_time(self):
        """Each hash should use a unique salt."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_verify_password_correct(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_empty(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False


class TestJWT:
    """Test JWT token creation and decoding."""

    def test_create_access_token_returns_string(self):
        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_subject(self):
        token = create_access_token(data={"sub": "admin"})
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert payload["sub"] == "admin"

    def test_create_access_token_has_expiry(self):
        token = create_access_token(data={"sub": "user1"})
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        token = create_access_token(
            data={"sub": "user1"},
            expires_delta=timedelta(minutes=5),
        )
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert "exp" in payload

    def test_invalid_token_raises_error(self):
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(
                "invalid.token.here",
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
