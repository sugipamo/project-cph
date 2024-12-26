use assert_cmd::Command;
use predicates::str::contains;
use std::fs;
use tempfile::TempDir;
use cph::Language;

struct TestContext {
    temp_dir: TempDir,
}

impl TestContext {
    fn new() -> Self {
        let temp_dir = TempDir::new().unwrap();
        Self { temp_dir }
    }

    fn run_in_docker(&self, args: &[&str], language: &str) -> assert_cmd::assert::Assert {
        let language = match Language::try_from(language) {
            Ok(lang) => lang,
            Err(e) => panic!("Invalid language: {}", e),
        };

        // バイナリをビルド
        Command::new("cargo")
            .args(["build"])
            .assert()
            .success();

        // バイナリをコピー
        let binary_path = assert_cmd::cargo::cargo_bin("cph");
        let target_binary = self.temp_dir.path().join("cph");
        fs::copy(&binary_path, &target_binary).unwrap();
        
        // 実行権限を付与
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            fs::set_permissions(&target_binary, fs::Permissions::from_mode(0o755)).unwrap();
        }

        // バイナリが存在することを確認
        assert!(target_binary.exists(), "Binary not found at {:?}", target_binary);
        
        let output = cph::docker::run_in_docker(
            self.temp_dir.path(),
            &language,
            &["/workspace/cph"].iter().chain(args).map(|s| *s).collect::<Vec<_>>(),
        ).unwrap();

        assert_cmd::assert::Assert::new(output)
    }
}

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