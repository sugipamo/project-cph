use assert_cmd::Command;
use predicates::str::contains;

fn run_command(args: &[&str]) -> assert_cmd::assert::Assert {
    Command::cargo_bin("cph")
        .unwrap()
        .args(args)
        .assert()
}

#[test]
fn test_invalid_language() {
    run_command(&["abc300", "invalid", "open", "a"])
        .failure()
        .stderr(contains("Invalid language"));
}

#[test]
fn test_invalid_command() {
    run_command(&["abc300", "rust", "invalid", "a"])
        .failure()
        .stderr(contains("Invalid command"));
} 