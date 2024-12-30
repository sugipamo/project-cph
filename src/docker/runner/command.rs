use std::process::Stdio;
use tokio::process::Command;
use uuid::Uuid;
use crate::docker::state::RunnerState;

pub struct DockerCommand {
    container_id: String,
    state: RunnerState,
    output: String,
    error: String,
}

impl DockerCommand {
    pub fn new() -> Self {
        Self {
            container_id: String::new(),
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
    pub async fn compile(&mut self, image: &str, compile_cmd: &[String], compile_dir: &str) -> Result<(), String> {
        println!("Compiling with command: {:?}", compile_cmd);
        
        let container_name = format!("compiler-{}", Uuid::new_v4());
        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg("--name")
            .arg(&container_name)
            .arg("-v")
            .arg(format!("{}:{}", compile_dir, compile_dir))
            .arg("-w")
            .arg(compile_dir)
            .arg(image)
            .args(compile_cmd)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let output = command.output().await;

        match output {
            Ok(output) => {
                let stderr = String::from_utf8_lossy(&output.stderr).to_string();
                if !stderr.is_empty() {
                    println!("Compilation error: {}", stderr);
                    Err(stderr)
                } else {
                    Ok(())
                }
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
        _timeout: u64,
        memory_limit: u64,
        compile_dir: Option<&str>,
    ) -> Result<String, String> {
        println!("Running container with image: {} and command: {:?}", image, run_cmd);
        
        let container_name = format!("runner-{}", Uuid::new_v4());
        let mut command = Command::new("docker");
        command
            .arg("run")
            .arg("--rm")
            .arg(format!("--memory={}m", memory_limit))
            .arg("--memory-swap=-1")
            .arg("--cpus=1.0")
            .arg("--network=none")
            .arg("--name")
            .arg(&container_name);

        if let Some(dir) = compile_dir {
            command
                .arg("-v")
                .arg(format!("{}:{}", dir, dir))
                .arg("-w")
                .arg(dir);
        }

        command
            .arg(image)
            .args(run_cmd);

        if compile_dir.is_none() {
            command.arg(source_code);
        }

        let output = command.output().await;

        match output {
            Ok(output) => {
                self.output = String::from_utf8_lossy(&output.stdout).to_string();
                self.error = String::from_utf8_lossy(&output.stderr).to_string();
                
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
        if self.container_id.is_empty() {
            return true;
        }

        println!("Stopping container: {}", self.container_id);
        
        let output = Command::new("docker")
            .args(["stop", &self.container_id])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .await;

        match output {
            Ok(_) => {
                println!("Container stopped successfully");
                self.state = RunnerState::Stop;
                true
            }
            Err(e) => {
                println!("Failed to stop container: {}", e);
                false
            }
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