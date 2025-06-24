-- Migration: Allow NULL values in system_config table
-- Version: 003
-- Description: Changes config_value column to allow NULL values to distinguish user-specified vs unspecified settings

-- SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table
-- Create new table with nullable config_value
CREATE TABLE system_config_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT,  -- Now allows NULL
    category TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copy existing data
INSERT INTO system_config_new (id, config_key, config_value, category, description, updated_at)
SELECT id, config_key, config_value, category, description, updated_at
FROM system_config;

-- Drop old table
DROP TABLE system_config;

-- Rename new table
ALTER TABLE system_config_new RENAME TO system_config;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);

-- Schema version will be updated automatically by SQLiteManager