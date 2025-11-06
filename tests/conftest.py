#!/usr/bin/env python3
"""
Pytest configuration for global environment defaults.
Ensures database modules see a consistent testing configuration before import.
"""

import os
from pathlib import Path


def _ensure_default_test_database() -> str:
    """Prepare a file-backed SQLite database path for isolated tests."""
    tests_dir = Path(__file__).parent
    tests_dir.mkdir(parents=True, exist_ok=True)
    db_path = tests_dir / ".pytest-db.sqlite"
    
    try:
        if db_path.exists():
            db_path.unlink()
    except OSError:
        # If removal fails we still attempt to reuse the file.
        pass
    
    return f"sqlite:///{db_path}"


DEFAULT_DB_URL = _ensure_default_test_database()

os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('ENVIRONMENT', 'testing')
os.environ.setdefault('DATABASE_URL', DEFAULT_DB_URL)
os.environ.setdefault('MVP_API_KEY', 'dev-test-api-key-123456')
os.environ.setdefault('SESSION_SECRET', 'dev-test-session-secret-1234567890abcdef')
