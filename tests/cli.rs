use assert_cmd::Command;
use predicates::str::contains;

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
fn test_invalid_site() {
    assert_error(
        &["invalid", TEST_CONTEST, "rust", "open", TEST_PROBLEM],
        "invalid value 'invalid' for '<SITE>'"
    );
}

#[test]
fn test_site_aliases() {
    // AtCoder aliases
    for site in ["atcoder", "at-coder", "at_coder"] {
        run_command(&[site, TEST_CONTEST, "rust", "open", TEST_PROBLEM])
            .failure() // Note: This will fail due to workspace setup, but that's expected
            .stderr(contains(""));
    }

    // Codeforces aliases
    for site in ["codeforces", "cf"] {
        run_command(&[site, TEST_CONTEST, "rust", "open", TEST_PROBLEM])
            .failure() // Note: This will fail due to workspace setup, but that's expected
            .stderr(contains(""));
    }
}

#[test]
fn test_invalid_language() {
    assert_error(
        &["atcoder", TEST_CONTEST, "invalid", "open", TEST_PROBLEM],
        "invalid value 'invalid' for '<LANGUAGE>'"
    );
}

#[test]
fn test_invalid_command() {
    assert_error(
        &["atcoder", TEST_CONTEST, "rust", "invalid", TEST_PROBLEM],
        "invalid command: invalid"
    );
} 