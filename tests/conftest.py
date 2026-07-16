import pytest
import os

# Set test environment variables before importing app modules
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_ci")
os.environ.setdefault("ENCRYPTION_KEY", "w2PlUngQ0X5vsF2BQdIQ0-29yHJ_B72UbKVKW15qBI4=")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///data/test_devops.db")
