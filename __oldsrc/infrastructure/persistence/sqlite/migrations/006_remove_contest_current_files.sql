-- Migration 006: Remove contest_current_files table and related indexes
-- This migration removes the over-engineered file tracking system in favor of simple filesystem-based management

-- Drop indexes first
DROP INDEX IF EXISTS idx_contest_current_files_context;
DROP INDEX IF EXISTS idx_contest_current_files_source;

-- Drop the main table
DROP TABLE IF EXISTS contest_current_files;