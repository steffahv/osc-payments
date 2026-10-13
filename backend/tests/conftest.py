"""Unit tests need no real credentials or database."""

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "unit-test-not-a-real-credential")
