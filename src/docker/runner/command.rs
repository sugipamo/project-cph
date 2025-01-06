use std::process::Stdio;
use tokio::process::Command;
use uuid::Uuid;
use std::time::Duration;
use std::env;
use tokio::time::timeout;
use std::path::Path;
use std::fs;
use std::os::unix::fs::PermissionsExt;

#[derive(Debug)]
pub struct DockerCommand {
    container_name: String,
}

impl DockerCommand {
    pub fn new() -> Self {
        Self {
            container_name: String::new(),
        }
    }

    fn ensure_directory_permissions(dir: &Path) -> Result<(), String> {
        let metadata = fs::metadata(dir)
            .map_err(|e| format!("メタデータの取得に失敗しました: {}", e))?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o777);
        fs::set_permissions(dir, perms)
            .map_err(|e| format!("パーミッションの設定に失敗しました: {}", e))?;
        Ok(())
    }

    pub async fn run_code(
        &self,
        image: &str,
        source_code: &str,
        memory_limit: u32,
        timeout_seconds: u32,
        mount_point: &str,
        extension: &str,
        compile_cmd: Option<&[String]>,
        run_cmd: &[String],
    ) -> Result<String, String> {
        // コンテナ名を生成
        let container_name = format!("runner-{}", Uuid::new_v4());

        // 一時ディレクトリを作成
        let temp_dir = std::env::temp_dir().join(format!("cph_{}", Uuid::new_v4()));
        fs::create_dir_all(&temp_dir)
            .map_err(|e| format!("一時ディレクトリの作成に失敗しました: {}", e))?;

        // ディレクトリのパーミッションを設定
        Self::ensure_directory_permissions(&temp_dir)?;

        // ソースコードを書き込み
        let source_file = temp_dir.join(format!("main.{}", extension));
        fs::write(&source_file, source_code)
            .map_err(|e| format!("ソースコードの書き込みに失敗しました: {}", e))?;

        // ファイルのパーミッションを設定
        let metadata = fs::metadata(&source_file)
            .map_err(|e| format!("ソースファイルのメタデータの取得に失敗しました: {}", e))?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o644);
        fs::set_permissions(&source_file, perms)
            .map_err(|e| format!("ソースファイルのパーミッションの設定に失敗しました: {}", e))?;

        // Dockerコマンドを構築
        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(&container_name)
            .arg("--memory")
            .arg(format!("{}m", memory_limit))
            .arg("--cpus")
            .arg("1.0")
            .arg("--network")
            .arg("none")
            .arg("-v")
            .arg(format!("{}:{}", temp_dir.display(), mount_point))
            .arg("-w")
            .arg(mount_point)
            .arg(image)
            .arg("sh")
            .arg("-c");

        // コマンドを構築
        let cmd = if let Some(compile_cmd) = compile_cmd {
            let compile_str = compile_cmd.iter()
                .map(|s| s.replace("main.rs", &format!("main.{}", extension)))
                .collect::<Vec<_>>()
                .join(" ");
            let run_str = run_cmd.iter()
                .map(|s| s.replace("main.rs", &format!("main.{}", extension)))
                .collect::<Vec<_>>()
                .join(" ");
            format!("ls -la && {} && {}", compile_str, run_str)
        } else {
            let run_str = run_cmd.iter()
                .map(|s| s.replace("main.rs", &format!("main.{}", extension)))
                .collect::<Vec<_>>()
                .join(" ");
            format!("ls -la && {}", run_str)
        };

        command.arg(cmd)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        // コマンドを実行（タイムアウト付き）
        println!("Running command: {:?}", command);
        let output = match timeout(Duration::from_secs(timeout_seconds.into()), command.output()).await {
            Ok(result) => result.map_err(|e| format!("コマンドの実行に失敗しました: {}", e))?,
            Err(_) => {
                self.stop_container().await;
                return Err("実行がタイムアウトしました".to_string());
            }
        };

        // 一時ディレクトリを削除
        let _ = fs::remove_dir_all(temp_dir);

        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }

    pub async fn compile(
        &mut self,
        image: &str,
        compile_cmd: &[String],
        compile_dir: &str,
        mount_point: &str,
        source_code: &str,
        extension: &str,
        require_files: &[String],
        env_vars: &[String],
        memory_limit: u32,
        timeout_seconds: u32,
    ) -> Result<(), String> {
        println!("Compiling with command: {:?}", compile_cmd);
        println!("Mount point: {}, Compile dir: {}", mount_point, compile_dir);
        
        // 現在のワーキングディレクトリを取得し、compile_dirへの絶対パスを構築
        let current_dir = env::current_dir()
            .map_err(|e| format!("カレントディレクトリの取得に失敗しました: {}", e))?;
        let absolute_compile_dir = current_dir.join(compile_dir);

        // コンパイルディレクトリを作成し、パーミッションを設定
        fs::create_dir_all(&absolute_compile_dir)
            .map_err(|e| format!("コンパイルディレクトリの作成に失敗しました: {}", e))?;
        Self::ensure_directory_permissions(&absolute_compile_dir)?;

        // 必要なファイルの存在チェック
        for required_file in require_files {
            let file_path = absolute_compile_dir.join(required_file);
            if !file_path.exists() {
                return Err(format!("必要なファイルが見つかりません: {}", required_file));
            }
        }

        // ソースファイルの配置
        let source_file = if !require_files.is_empty() {
            let src_dir = absolute_compile_dir.join("src");
            fs::create_dir_all(&src_dir)
                .map_err(|e| format!("ソースディレクトリの作成に失敗しました: {}", e))?;
            Self::ensure_directory_permissions(&src_dir)?;
            src_dir.join(format!("main.{}", extension))
        } else {
            absolute_compile_dir.join(format!("main.{}", extension))
        };

        fs::write(&source_file, source_code)
            .map_err(|e| format!("ソースコードの書き込みに失敗しました: {}", e))?;
        
        let container_name = format!("compiler-{}", Uuid::new_v4());
        self.container_name = container_name.clone();

        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(&container_name)
            .arg("-m")
            .arg(format!("{}m", memory_limit))
            .arg("--memory-swap")
            .arg(format!("{}m", memory_limit))
            .arg("-v")
            .arg(format!("{}:{}", absolute_compile_dir.display(), mount_point))
            .arg("-w")
            .arg(mount_point);

        // 環境変数の設定
        for env_var in env_vars {
            command.arg("-e").arg(env_var);
        }

        command
            .arg(image)
            .args(compile_cmd)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        println!("Running compile command: {:?}", command);
        let output = match timeout(Duration::from_secs(timeout_seconds.into()), command.output()).await {
            Ok(result) => result.map_err(|e| format!("コンパイルコマンドの実行に失敗しました: {}", e))?,
            Err(_) => {
                self.stop_container().await;
                return Err("コンパイルがタイムアウトしました".to_string());
            }
        };

        if !output.status.success() {
            let error = String::from_utf8_lossy(&output.stderr);
            return Err(format!("コンパイルに失敗しました: {}", error));
        }

        Ok(())
    }

    pub async fn check_image(&self, image: &str) -> bool {
        let output = Command::new("docker")
            .arg("image")
            .arg("inspect")
            .arg(image)
            .output()
            .await;

        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }

    pub async fn pull_image(&self, image: &str) -> bool {
        let output = Command::new("docker")
            .arg("pull")
            .arg(image)
            .output()
            .await;

        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }

    pub async fn stop_container(&self) -> bool {
        if self.container_name.is_empty() {
            return true;
        }

        let output = Command::new("docker")
            .arg("stop")
            .arg(&self.container_name)
            .output()
            .await;

        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }

    pub async fn inspect_directory(&self, image: &str, mount_point: &str) -> Result<String, String> {
        let container_name = format!("inspector-{}", Uuid::new_v4());
        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(&container_name)
            .arg("-v")
            .arg(format!("{}:{}", mount_point, mount_point))
            .arg("-w")
            .arg(mount_point)
            .arg(image)
            .arg("ls")
            .arg("-la")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let output = command.output().await
            .map_err(|e| format!("Failed to execute inspect command: {}", e))?;

        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }
} 