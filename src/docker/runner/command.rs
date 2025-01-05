use std::process::Stdio;
use tokio::process::Command;
use uuid::Uuid;
use crate::docker::state::RunnerState;
use std::time::Duration;
use std::env;
use tokio::time::timeout;

pub struct DockerCommand {
    container_name: String,
    state: RunnerState,
    output: String,
    error: String,
}

impl DockerCommand {
    pub fn new() -> Self {
        Self {
            container_name: String::new(),
            state: RunnerState::Ready,
            output: String::new(),
            error: String::new(),
        }
    }

    pub async fn run_code(&mut self, image: &str, source_code: &str) -> Result<String, String> {
        // コンテナ名を生成
        let container_name = format!("runner-{}", Uuid::new_v4());
        self.container_name = container_name.clone();

        // 一時ディレクトリを作成
        let temp_dir = env::temp_dir().join(&container_name);
        std::fs::create_dir_all(&temp_dir)
            .map_err(|e| format!("一時ディレクトリの作成に失敗しました: {}", e))?;

        // ソースコードを書き込み
        let source_file = temp_dir.join("main.rs");
        std::fs::write(&source_file, source_code)
            .map_err(|e| format!("ソースコードの書き込みに失敗しました: {}", e))?;

        // Dockerコマンドを構築
        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(&container_name)
            .arg("-v")
            .arg(format!("{}:/code", temp_dir.display()))
            .arg("-w")
            .arg("/code")
            .arg(image)
            .arg("sh")
            .arg("-c")
            .arg("rustc main.rs && ./main")
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        // コマンドを実行
        println!("Running command: {:?}", command);
        let output = match timeout(Duration::from_secs(10), command.output()).await {
            Ok(result) => result.map_err(|e| format!("コマンドの実行に失敗しました: {}", e))?,
            Err(_) => {
                self.stop_container().await;
                return Err("実行がタイムアウトしました".to_string());
            }
        };

        // 一時ディレクトリを削除
        let _ = std::fs::remove_dir_all(temp_dir);

        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }

    // コンパイル実行
    pub async fn compile(
        &mut self,
        image: &str,
        compile_cmd: &[String],
        compile_dir: &str,
        mount_point: &str,
        source_code: &str,
        extension: String,
        require_files: Vec<String>,
        env_vars: Vec<String>,
    ) -> Result<(), String> {
        println!("Compiling with command: {:?}", compile_cmd);
        println!("Mount point: {}, Compile dir: {}", mount_point, compile_dir);
        
        // 現在のワーキングディレクトリを取得し、compile_dirへの絶対パスを構築
        let current_dir = env::current_dir()
            .map_err(|e| format!("Failed to get current directory: {}", e))?;
        let absolute_compile_dir = current_dir.join(compile_dir);

        // ソースコードをファイルに書き込む
        use std::fs;
        fs::create_dir_all(&absolute_compile_dir)
            .map_err(|e| format!("Failed to create compile directory: {}", e))?;

        // 必要なファイルの存在チェック
        for required_file in &require_files {
            let file_path = absolute_compile_dir.join(required_file);
            if !file_path.exists() {
                return Err(format!("Required file not found: {}", required_file));
            }
        }

        // ソースファイルの配置
        let source_file = if !require_files.is_empty() {
            // 必要なファイルがある場合（例：Cargoプロジェクト）はsrcディレクトリを作成
            let src_dir = absolute_compile_dir.join("src");
            fs::create_dir_all(&src_dir)
                .map_err(|e| format!("Failed to create source directory: {}", e))?;
            src_dir.join(format!("main.{}", extension))
        } else {
            // その他の言語の場合は直接コンパイルディレクトリに配置
            absolute_compile_dir.join(format!("main.{}", extension))
        };

        fs::write(&source_file, source_code)
            .map_err(|e| format!("Failed to write source code: {}", e))?;
        
        let container_name = format!("compiler-{}", Uuid::new_v4());
        self.container_name = container_name.clone();

        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(&container_name)
            .arg("-v")
            .arg(format!("{}:{}", absolute_compile_dir.display(), mount_point))
            .arg("-w")
            .arg(mount_point);

        // 環境変数の設定
        for env_var in &env_vars {
            command.arg("-e").arg(env_var);
        }

        command
            .arg(image)
            .args(compile_cmd)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        println!("Running compile command: {:?}", command);
        let output = command.output().await
            .map_err(|e| format!("Failed to execute compile command: {}", e))?;

        if !output.status.success() {
            let error = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Compilation failed: {}", error));
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