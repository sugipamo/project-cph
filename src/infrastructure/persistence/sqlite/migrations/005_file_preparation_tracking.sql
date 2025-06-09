-- Migration 005: Add file_preparation_operations table for tracking test file movements
-- This table tracks files moved during file preparation (e.g., test files from workspace to contest_current)

CREATE TABLE file_preparation_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL,
    contest_name TEXT NOT NULL,
    problem_name TEXT NOT NULL,
    operation_type TEXT NOT NULL,        -- 'move_test_files', 'cleanup', etc.
    source_path TEXT NOT NULL,           -- Source file/directory path  
    destination_path TEXT NOT NULL,      -- Destination file/directory path
    file_count INTEGER DEFAULT 0,        -- Number of files processed
    success BOOLEAN NOT NULL DEFAULT 0,  -- Operation success status
    error_message TEXT,                  -- Error message if failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for efficient querying by contest context
    UNIQUE(language_name, contest_name, problem_name, operation_type, source_path)
);

-- Index for efficient querying by contest context
CREATE INDEX idx_file_preparation_context 
ON file_preparation_operations(language_name, contest_name, problem_name);

-- Index for querying by operation type
CREATE INDEX idx_file_preparation_operation 
ON file_preparation_operations(operation_type);

-- Index for querying by timestamp
CREATE INDEX idx_file_preparation_created 
ON file_preparation_operations(created_at);