use std::process::Stdio;
use tokio::process::Command;
use uuid::Uuid;
use crate::docker::state::RunnerState;
use std::time::Duration;
use std::env;

pub struct DockerCommand {
    container_name: String,
    state: RunnerState,
    output: String,
    error: String,
}

#[derive(Debug, Clone)]
pub struct CompileConfig {
    pub extension: String,
    pub require_files: Vec<String>,
    pub env_vars: Vec<String>,
}

impl CompileConfig {
    pub fn new(extension: String, require_files: Vec<String>, env_vars: Vec<String>) -> Self {
        Self {
            extension,
            require_files,
            env_vars,
        }
    }

    pub fn from_config(config_builder: &crate::config::Config, language: &str) -> Result<Self, String> {
        let extension = config_builder.get::<String>(&format!("{}.extension", language))
            .map_err(|e| format!("拡張子の取得に失敗しました: {}", e))?;

        let require_files = if language == "rust" {
            vec!["Cargo.toml".to_string()]
        } else {
            vec![]
        };

        let env_vars = config_builder.get::<Vec<String>>(&format!("{}.runner.env_vars", language))
            .map_err(|e| format!("環境変数設定の取得に失敗しました: {}", e))?;

        Ok(Self::new(extension, require_files, env_vars))
    }
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

    // イメージの存在確認
    pub async fn check_image(&self, image: &str) -> bool {
        println!("Checking for image: {}", image);
        
        let output = Command::new("docker")
            .args(["images", "-q", image])
            .stdout(Stdio::piped())
            .output()
            .await;

        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                !stdout.trim().is_empty()
            }
            Err(e) => {
                println!("Failed to check image: {}", e);
                false
            }
        }
    }

    // イメージの取得
    pub async fn pull_image(&self, image: &str) -> bool {
        println!("Pulling image: {}", image);
        
        let output = Command::new("docker")
            .args(["pull", image])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await;

        match output {
            Ok(output) => {
                let stderr = String::from_utf8_lossy(&output.stderr);
                if stderr.contains("Error") {
                    println!("Failed to pull image: {}", stderr);
                    false
                } else {
                    true
                }
            }
            Err(e) => {
                println!("Failed to pull image: {}", e);
                false
            }
        }
    }

    // コンテイル言語用のコンパイル実行
    pub async fn compile(
        &mut self,
        image: &str,
        compile_cmd: &[String],
        compile_dir: &str,
        mount_point: &str,
        source_code: &str,
        config: CompileConfig,
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
        for required_file in &config.require_files {
            let file_path = absolute_compile_dir.join(required_file);
            if !file_path.exists() {
                return Err(format!("Required file not found: {}", required_file));
            }
        }

        // ソースファイルの配置
        let source_file = if !config.require_files.is_empty() {
            // 必要なファイルがある場合（例：Cargoプロジェクト）はsrcディレクトリを作成
            let src_dir = absolute_compile_dir.join("src");
            fs::create_dir_all(&src_dir)
                .map_err(|e| format!("Failed to create source directory: {}", e))?;
            src_dir.join(format!("main.{}", config.extension))
        } else {
            // その他の言語の場合は直接コンパイルディレクトリに配置
            absolute_compile_dir.join(format!("main.{}", config.extension))
        };

        fs::write(&source_file, source_code)
            .map_err(|e| format!("Failed to write source code: {}", e))?;
        
        let container_name = format!("compiler-{}", Uuid::new_v4());
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
        for env_var in &config.env_vars {
            command.arg("-e").arg(env_var);
        }

        command
            .arg(image)
            .args(compile_cmd)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        println!("Running compile command: {:?}", command);
        let output = command.output().await;

        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout).to_string();
                let stderr = String::from_utf8_lossy(&output.stderr).to_string();
                
                // コンパイルエラーの場合
                if !output.status.success() {
                    println!("Compilation error: {}", stderr);
                    return Err(stderr);
                }
                
                // 標準エラー出力があるが、コンパイルは成功している場合（警告など）
                if !stderr.is_empty() {
                    println!("Compilation warnings: {}", stderr);
                }
                
                // 標準出力がある場合は表示
                if !stdout.is_empty() {
                    println!("Compilation output: {}", stdout);
                }
                
                Ok(())
            }
            Err(e) => {
                println!("Failed to compile: {}", e);
                Err(e.to_string())
            }
        }
    }

    // コンテナの作成と実行
    pub async fn run_container(
        &mut self,
        image: &str,
        run_cmd: &[String],
        source_code: &str,
        timeout: u64,
        memory_limit: u64,
        compile_dir: Option<&str>,
        mount_point: &str,
    ) -> Result<String, String> {
        println!("Running container with image: {} and command: {:?}", image, run_cmd);
        if let Some(dir) = compile_dir {
            println!("Mount point: {}, Compile dir: {}", mount_point, dir);
        }
        
        self.container_name = format!("runner-{}", Uuid::new_v4());
        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg(format!("-m={}m", memory_limit))
            .arg("--cpus=1.0")
            .arg("--network=none")
            .arg("--name")
            .arg(&self.container_name);

        if let Some(dir) = compile_dir {
            // 現在のワーキングディレクトリを取得し、compile_dirへの絶対パスを構築
            let current_dir = env::current_dir()
                .map_err(|e| format!("Failed to get current directory: {}", e))?;
            let absolute_compile_dir = current_dir.join(dir);
            
            command
                .arg("-v")
                .arg(format!("{}:{}", absolute_compile_dir.display(), mount_point))
                .arg("-w")
                .arg(mount_point);
        }

        command
            .arg(image)
            .args(run_cmd);

        // コンパイルが不要な言語の場合のみソースコードを直接渡す
        if compile_dir.is_none() {
            command.arg(source_code);
        }

        // タイムアウト用のスレッドを起動
        let container_name_clone = self.container_name.clone();
        let timeout_handle = tokio::spawn(async move {
            tokio::time::sleep(Duration::from_secs(timeout)).await;
            let stop_command = Command::new("docker")
                .args(["stop", &container_name_clone])
                .output()
                .await;
            if let Err(e) = stop_command {
                println!("Failed to stop container after timeout: {}", e);
            }
        });

        let output = command.output().await;
        timeout_handle.abort();  // コンテナが終了したらタイムアウトハンドラを中止

        match output {
            Ok(output) => {
                self.output = String::from_utf8_lossy(&output.stdout).to_string();
                self.error = String::from_utf8_lossy(&output.stderr).to_string();
                
                // 終了コードを確認
                if !output.status.success() {
                    let exit_code = output.status.code().unwrap_or(-1);
                    println!("Container exited with code: {}", exit_code);
                    if exit_code == 137 || self.error.contains("OOM") {
                        self.state = RunnerState::Error;
                        return Err("Container killed by OOM killer".to_string());
                    }
                }
                
                if !self.error.is_empty() {
                    println!("Container stderr: {}", self.error);
                    self.state = RunnerState::Error;
                    Err(self.error.clone())
                } else {
                    println!("Container stdout: {}", self.output);
                    self.state = RunnerState::Running;
                    Ok(self.output.clone())
                }
            }
            Err(e) => {
                println!("Failed to run container: {}", e);
                self.state = RunnerState::Error;
                Err(e.to_string())
            }
        }
    }

    // コンテナの停止
    pub async fn stop_container(&mut self) -> bool {
        if self.container_name.is_empty() {
            return true;
        }

        println!("Stopping container: {}", self.container_name);
        
        let output = Command::new("docker")
            .args(["stop", &self.container_name])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await;

        match output {
            Ok(_) => {
                println!("Container stopped successfully");
                self.state = RunnerState::Stop;
                self.container_name.clear();  // コンテナ名をクリア
                true
            }
            Err(e) => {
                println!("Failed to stop container: {}", e);
                false
            }
        }
    }

    pub async fn inspect_directory(&mut self, image: &str, dir_path: &str) -> Result<String, String> {
        // 一時的なコンテナ名を生成
        self.container_name = format!("inspector-{}", Uuid::new_v4());

        // コンテナを起動してディレクトリ構造を確認
        let output = Command::new("docker")
            .args([
                "run",
                "--rm",
                "--name",
                &self.container_name,
                image,
                "sh",
                "-c",
                &format!("ls -la {}", dir_path),
            ])
            .output()
            .await
            .map_err(|e| e.to_string())?;

        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            Err(String::from_utf8_lossy(&output.stderr).to_string())
        }
    }

    #[allow(dead_code)]
    pub fn get_state(&self) -> RunnerState {
        self.state.clone()
    }

    #[allow(dead_code)]
    pub fn get_output(&self) -> &str {
        &self.output
    }

    #[allow(dead_code)]
    pub fn get_error(&self) -> &str {
        &self.error
    }
} 