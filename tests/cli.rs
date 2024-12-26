use assert_cmd::Command;
use predicates::str::contains;
use cph::{INVALID_LANGUAGE_ERROR, INVALID_COMMAND_ERROR};

const TEST_CONTEST: &str = "abc300";
const TEST_PROBLEM: &str = "a";

fn run_command(args: &[&str]) -> assert_cmd::assert::Assert {
    Command::cargo_bin("cph")
        .unwrap()
        .args(args)
        .assert()
}

fn assert_error(args: &[&str], expected_error: &str) {
    run_command(args)
        .failure()
        .stderr(contains(expected_error));
}

#[test]
fn test_invalid_language() {
    assert_error(
        &[TEST_CONTEST, "invalid", "open", TEST_PROBLEM],
        INVALID_LANGUAGE_ERROR
    );
}

#[test]
fn test_invalid_command() {
    assert_error(
        &[TEST_CONTEST, "rust", "invalid", TEST_PROBLEM],
        INVALID_COMMAND_ERROR
    );
} 