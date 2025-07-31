#!/usr/bin/env python3
"""
Test suite for Student Success Prediction MVP system.

Comprehensive tests covering:
- Database operations (PostgreSQL and SQLite fallback)
- API endpoints and authentication
- File upload and CSV processing
- K-12 ultra-advanced model predictions
- Explainable AI functionality
- Batch database operations performance
- Error handling and edge cases
"""

# Test configuration
TEST_DATABASE_URL = "sqlite:///./test_mvp.db"
TEST_API_BASE_URL = "http://localhost:8001"
TEST_API_KEY = "test-key-12345"

# Test data paths
TEST_DATA_DIR = "tests/fixtures"
SAMPLE_CSV_PATH = f"{TEST_DATA_DIR}/sample_gradebook.csv"
CANVAS_CSV_PATH = f"{TEST_DATA_DIR}/canvas_gradebook.csv"
INVALID_CSV_PATH = f"{TEST_DATA_DIR}/invalid_file.csv"