mod common;

use common::test_helpers::TestEnvironment;
use common::fixtures;

#[test]
fn test_environment_setup() {
    let env = TestEnvironment::new();
    
    // Create a test file
    env.create_file("test.txt", "Hello, World!");
    
    // Verify file exists and has correct content
    assert!(env.file_exists("test.txt"));
    assert_eq!(env.read_file("test.txt"), "Hello, World!");
}

#[test]
fn test_nested_file_creation() {
    let env = TestEnvironment::new();
    
    // Create a nested file
    env.create_file("nested/dir/file.txt", "Nested content");
    
    // Verify file exists
    assert!(env.file_exists("nested/dir/file.txt"));
    assert_eq!(env.read_file("nested/dir/file.txt"), "Nested content");
}

#[test]
fn test_config_fixture() {
    let env = TestEnvironment::new();
    
    // Use fixture to create config file
    env.create_file("config.toml", fixtures::SAMPLE_CONFIG);
    
    // Verify config exists
    assert!(env.file_exists("config.toml"));
    assert!(env.read_file("config.toml").contains("test-app"));
}