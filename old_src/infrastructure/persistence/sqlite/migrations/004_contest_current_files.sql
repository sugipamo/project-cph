-- Migration 004: Add contest_current_files table for tracking file structure
-- This table maintains the file structure of contest_current in 1NF

CREATE TABLE contest_current_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL,
    contest_name TEXT NOT NULL,
    problem_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,  -- Path relative to contest_current directory
    source_type TEXT NOT NULL,    -- 'template' or 'stock' 
    source_path TEXT NOT NULL,    -- Original source file path
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique file tracking per contest context
    UNIQUE(language_name, contest_name, problem_name, relative_path)
);

-- Index for efficient querying by contest context
CREATE INDEX idx_contest_current_files_context 
ON contest_current_files(language_name, contest_name, problem_name);

-- Index for querying by source type
CREATE INDEX idx_contest_current_files_source 
ON contest_current_files(source_type);