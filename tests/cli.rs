use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;
use cph::docker::DockerConfig;
use std::path::PathBuf;
use cph::{Error, Language};

struct TestContext {
    temp_dir: TempDir,
    abc_dir: std::path::PathBuf,
}

impl TestContext {
    fn new() -> Self {
        let temp_dir = TempDir::new().unwrap();
        let abc_dir = temp_dir.path().join("workspace/abc/abc300");
        
        // 必要なディレクトリを作成
        fs::create_dir_all(&abc_dir).unwrap();
        fs::create_dir_all(abc_dir.join("test")).unwrap();
        fs::create_dir_all(abc_dir.join("template")).unwrap();
        
        Self {
            temp_dir,
            abc_dir,
        }
    }

    fn create_template(&self, content: &str) {
        let template_dir = self.abc_dir.join("template");
        fs::create_dir_all(&template_dir).unwrap();
        fs::write(template_dir.join("main.rs"), content).unwrap();
    }

    fn run_in_docker(&self, args: &[&str], language: &str) -> assert_cmd::assert::Assert {
        let language = match Language::try_from(language) {
            Ok(lang) => lang,
            Err(e) => panic!("Invalid language: {}", e),
        };
        let image = DockerConfig::get_image(&language);

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
        
        // ディレクトリ構造を確認
        println!("Workspace structure:");
        if let Ok(output) = Command::new("ls")
            .args(["-la", self.temp_dir.path().to_str().unwrap()])
            .output() {
            println!("{}", String::from_utf8_lossy(&output.stdout));
        }

        Command::new("docker")
            .args([
                "run",
                "--rm",
                "--memory",
                &DockerConfig::get().memory_limit,
                "--memory-swap",
                &DockerConfig::get().memory_limit,
                "-v",
                &format!("{}:/workspace", self.temp_dir.path().display()),
                "-w",
                "/workspace",
                &image,
                "/workspace/cph",
            ])
            .args(args)
            .assert()
    }
}

// 基本的なコマンドライン引数のテストはDocker外で実行
#[test]
fn test_invalid_language() {
    Command::cargo_bin("cph")
        .unwrap()
        .args(["abc300", "invalid", "open", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid language"));
}

#[test]
fn test_invalid_command() {
    Command::cargo_bin("cph")
        .unwrap()
        .args(["abc300", "rust", "invalid", "a"])
        .assert()
        .failure()
        .stderr(predicate::str::contains("Invalid command"));
}

// 以下のテストは段階的に追加していきます 