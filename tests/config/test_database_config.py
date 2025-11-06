#!/usr/bin/env python3
"""
Configuration loader tests for database settings.
Ensures PostgreSQL defaults and SQLite restrictions behave as expected.
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure project root on path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.mvp.config import ConfigurationLoader, Environment


def _clear_database_env(monkeypatch):
    """Remove DB-related env vars before each scenario."""
    for var in ['DATABASE_URL', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'TESTING']:
        monkeypatch.delenv(var, raising=False)


def test_component_config_defaults_localhost(monkeypatch):
    """Ensure host defaults to localhost when omitted."""
    _clear_database_env(monkeypatch)
    monkeypatch.setenv('DB_USER', 'tester')
    monkeypatch.setenv('DB_PASSWORD', 'secret')
    monkeypatch.setenv('DB_NAME', 'demo_db')
    
    db_config = ConfigurationLoader._load_database_config(Environment.DEVELOPMENT)
    assert db_config.url == "postgresql://tester:secret@localhost:5432/demo_db"


def test_missing_postgres_credentials_raise(monkeypatch):
    """Missing credentials should raise descriptive error."""
    _clear_database_env(monkeypatch)
    monkeypatch.setenv('DB_USER', 'tester')
    
    with pytest.raises(ValueError, match="Missing PostgreSQL environment variables"):
        ConfigurationLoader._load_database_config(Environment.DEVELOPMENT)


def test_sqlite_only_allowed_in_tests(monkeypatch):
    """SQLite URLs should be rejected outside of test mode."""
    _clear_database_env(monkeypatch)
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///tmp/test.db')
    
    with pytest.raises(ValueError, match="SQLite databases are only permitted during automated tests"):
        ConfigurationLoader._load_database_config(Environment.DEVELOPMENT)


def test_sqlite_rejected_in_production(monkeypatch):
    """Production environment must reject SQLite even in testing mode."""
    _clear_database_env(monkeypatch)
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///tmp/test.db')
    monkeypatch.setenv('TESTING', 'true')
    
    with pytest.raises(ValueError, match="Production must use PostgreSQL"):
        ConfigurationLoader._load_database_config(Environment.PRODUCTION)


def test_sqlite_allowed_when_testing_flag_set(monkeypatch):
    """SQLite can be used when explicit testing flag is enabled."""
    _clear_database_env(monkeypatch)
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///tmp/test.db')
    monkeypatch.setenv('TESTING', 'true')
    
    db_config = ConfigurationLoader._load_database_config(Environment.TESTING)
    assert db_config.url == 'sqlite:///tmp/test.db'
