-- Student Success Prediction Database Initialization
-- This script runs when PostgreSQL container starts for the first time

-- Create database if it doesn't exist (PostgreSQL creates it via POSTGRES_DB env var)
-- But we can set permissions and extensions here

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For better indexing

-- Set timezone
SET timezone = 'UTC';

-- Create schema for audit logs (optional organization)
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions to postgres user (for development)
GRANT ALL PRIVILEGES ON DATABASE student_success TO postgres;

-- Create a read-only user for analytics (future use)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'analytics_user') THEN
        CREATE USER analytics_user WITH PASSWORD 'analytics_readonly';
    END IF;
END
$$;

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Success message
SELECT 'Student Success Prediction database initialized successfully!' as message;