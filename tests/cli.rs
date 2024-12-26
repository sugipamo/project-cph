use assert_cmd::Command;
use predicates::str::contains;

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
fn test_invalid_site() {
    assert_error(
        &["invalid", "login"],
        "invalid value 'invalid' for '<SITE>'"
    );
}

#[test]
fn test_invalid_command() {
    assert_error(
        &["atcoder", "invalid"],
        "invalid command: invalid"
    );
}

#[test]
fn test_open_command_requires_args() {
    assert_error(
        &["atcoder", "open"],
        "the following required arguments were not provided:"
    );
} 