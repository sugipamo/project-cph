-- Migration: Add Docker container and image tracking tables
-- Version: 002
-- Description: Adds tables for tracking Docker containers, images, and their lifecycle

-- Docker images table
CREATE TABLE IF NOT EXISTS docker_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tag TEXT DEFAULT 'latest',
    image_id TEXT,
    dockerfile_hash TEXT,
    build_command TEXT,
    build_status TEXT DEFAULT 'pending',
    build_time_ms INTEGER,
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, tag)
);

-- Docker containers table
CREATE TABLE IF NOT EXISTS docker_containers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_name TEXT NOT NULL UNIQUE,
    container_id TEXT,
    image_name TEXT NOT NULL,
    image_tag TEXT DEFAULT 'latest',
    status TEXT DEFAULT 'created',
    language TEXT,
    contest_name TEXT,
    problem_name TEXT,
    env_type TEXT,
    volumes TEXT,  -- JSON array of volume mappings
    environment TEXT,  -- JSON object of environment variables
    ports TEXT,  -- JSON array of port mappings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    removed_at TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_name, image_tag) REFERENCES docker_images(name, tag)
);

-- Container lifecycle events table
CREATE TABLE IF NOT EXISTS container_lifecycle_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_name TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- created, started, stopped, removed, error
    event_data TEXT,  -- JSON object with event details
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (container_name) REFERENCES docker_containers(container_name)
);

-- System configuration table (replaces system_info.json)
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,  -- JSON string
    category TEXT,  -- command, language, docker, output, etc.
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_docker_containers_status ON docker_containers(status);
CREATE INDEX IF NOT EXISTS idx_docker_containers_language ON docker_containers(language);
CREATE INDEX IF NOT EXISTS idx_docker_containers_last_used ON docker_containers(last_used_at);
CREATE INDEX IF NOT EXISTS idx_docker_images_name ON docker_images(name);
CREATE INDEX IF NOT EXISTS idx_container_events_container ON container_lifecycle_events(container_name);
CREATE INDEX IF NOT EXISTS idx_container_events_timestamp ON container_lifecycle_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);

-- Update schema version
UPDATE schema_version SET version = 2 WHERE id = 1;