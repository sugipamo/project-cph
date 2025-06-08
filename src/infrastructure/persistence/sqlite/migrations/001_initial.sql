-- Initial schema for operation history tracking
-- Migration 001: Create core tables for operation and session management

-- Operations table for tracking all operations
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    command TEXT NOT NULL,
    language TEXT,
    contest_name TEXT,
    problem_name TEXT,
    env_type TEXT,
    result TEXT,
    execution_time_ms INTEGER,
    stdout TEXT,
    stderr TEXT,
    return_code INTEGER,
    details TEXT, -- JSON for additional details
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table for tracking work sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_end DATETIME,
    language TEXT,
    contest_name TEXT,
    problem_name TEXT,
    total_operations INTEGER DEFAULT 0,
    successful_operations INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Language usage statistics
CREATE TABLE IF NOT EXISTS language_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT NOT NULL UNIQUE,
    total_operations INTEGER DEFAULT 0,
    successful_operations INTEGER DEFAULT 0,
    last_used DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Contest progress tracking
CREATE TABLE IF NOT EXISTS contest_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_name TEXT NOT NULL,
    problem_name TEXT NOT NULL,
    language TEXT NOT NULL,
    status TEXT DEFAULT 'working', -- working, solved, abandoned
    first_attempt DATETIME,
    last_attempt DATETIME,
    total_attempts INTEGER DEFAULT 0,
    successful_submissions INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contest_name, problem_name, language)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_operations_timestamp ON operations(timestamp);
CREATE INDEX IF NOT EXISTS idx_operations_command ON operations(command);
CREATE INDEX IF NOT EXISTS idx_operations_language ON operations(language);
CREATE INDEX IF NOT EXISTS idx_operations_contest ON operations(contest_name, problem_name);

CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_sessions_language ON sessions(language);

CREATE INDEX IF NOT EXISTS idx_language_stats_language ON language_stats(language);
CREATE INDEX IF NOT EXISTS idx_language_stats_last_used ON language_stats(last_used);

CREATE INDEX IF NOT EXISTS idx_contest_progress_contest ON contest_progress(contest_name, problem_name);
CREATE INDEX IF NOT EXISTS idx_contest_progress_language ON contest_progress(language);
CREATE INDEX IF NOT EXISTS idx_contest_progress_status ON contest_progress(status);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial version
INSERT OR REPLACE INTO schema_version (id, version) VALUES (1, 1);