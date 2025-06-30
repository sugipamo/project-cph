mod common;

use common::test_helpers::TestEnvironment;
use common::fixtures;

#[test]
fn test_environment_setup() {
    let env = TestEnvironment::new().expect("Failed to create test environment");
    
    // Create a test file
    env.create_file("test.txt", "Hello, World!").expect("Failed to create file");
    
    // Verify file exists and has correct content
    assert!(env.file_exists("test.txt"));
    assert_eq!(env.read_file("test.txt").expect("Failed to read file"), "Hello, World!");
}

#[test]
fn test_nested_file_creation() {
    let env = TestEnvironment::new().expect("Failed to create test environment");
    
    // Create a nested file
    env.create_file("nested/dir/file.txt", "Nested content").expect("Failed to create file");
    
    // Verify file exists
    assert!(env.file_exists("nested/dir/file.txt"));
    assert_eq!(env.read_file("nested/dir/file.txt").expect("Failed to read file"), "Nested content");
}

#[test]
fn test_config_fixture() {
    let env = TestEnvironment::new().expect("Failed to create test environment");
    
    // Use fixture to create config file
    env.create_file("config.toml", fixtures::SAMPLE_CONFIG).expect("Failed to create config");
    
    // Verify config exists
    assert!(env.file_exists("config.toml"));
    assert!(env.read_file("config.toml").expect("Failed to read config").contains("test-app"));
}