use std::path::Path;
use std::process::Command;
use std::time::Duration;
use tokio::process::Command as TokioCommand;
use tokio::io::AsyncWriteExt;
use std::process::Stdio;
use tokio::time::timeout;
use once_cell::sync::Lazy;
use std::path::PathBuf;

use crate::error::{Error, Result, DockerError};
use crate::{Language, DEFAULT_TIMEOUT_SECS, DEFAULT_MEMORY_LIMIT};

static DOCKER_CONFIG: Lazy<DockerConfig> = Lazy::new(|| DockerConfig {
    timeout_seconds: DEFAULT_TIMEOUT_SECS,
    memory_limit: DEFAULT_MEMORY_LIMIT.to_string(),
});

pub struct DockerConfig {
    pub timeout_seconds: u64,
    pub memory_limit: String,
}

impl DockerConfig {
    pub fn get() -> &'static Self {
        &DOCKER_CONFIG
    }

    pub fn get_image(language: &Language) -> String {
        language.docker_image().to_string()
    }

    fn get_compile_mount(language: &Language) -> String {
        let compile_dir = match language {
            Language::Rust => "compile/rust",
            Language::PyPy => "compile/pypy",
        };
        let absolute_path = std::env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(compile_dir);
        format!("{}:/compile", absolute_path.display())
    }
}

pub async fn execute_program(
    program: &str,
    args: &[&str],
    stdin: Option<String>,
) -> Result<(String, String)> {
    let mut command = TokioCommand::new(program);
    command.args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = command.spawn()
        .map_err(|e| Error::Docker(DockerError::failed("spawn process", e)))?;

    if let Some(input) = stdin {
        if let Some(mut stdin) = child.stdin.take() {
            if let Err(e) = stdin.write_all(input.as_bytes()).await {
                return Err(Error::Docker(DockerError::failed("write to stdin", e)));
            }
        }
    }

    let config = DockerConfig::get();
    match timeout(Duration::from_secs(config.timeout_seconds), child.wait_with_output()).await {
        Ok(Ok(output)) => Ok((
            String::from_utf8_lossy(&output.stdout).into_owned(),
            String::from_utf8_lossy(&output.stderr).into_owned(),
        )),
        Ok(Err(e)) => Err(Error::Docker(DockerError::failed("execute program", e))),
        Err(_) => Err(Error::Docker(DockerError::Timeout(config.timeout_seconds))),
    }
}

pub fn run_in_docker(
    workspace_dir: &Path,
    language: &Language,
    cmd: &[&str],
) -> Result<std::process::Output> {
    let config = DockerConfig::get();
    let workspace_path = workspace_dir.canonicalize()
        .unwrap_or_else(|_| workspace_dir.to_path_buf());

    Command::new("docker")
        .args([
            "run",
            "--rm",
            "--memory",
            &config.memory_limit,
            "--memory-swap",
            &config.memory_limit,
            "-v",
            &format!("{}:/workspace", workspace_path.display()),
            "-v",
            &DockerConfig::get_compile_mount(language),
            "-w",
            "/workspace",
            &DockerConfig::get_image(language),
        ])
        .args(cmd)
        .output()
        .map_err(|e| Error::Docker(DockerError::failed("run docker", e)))
}

// online judge tool用のDockerイメージ名
pub const OJT_DOCKER_IMAGE: &str = "cph-oj";

// online judge toolのコマンドを実行する関数
pub async fn run_oj_tool(
    workspace_dir: &Path,
    args: &[&str],
) -> Result<(String, String)> {
    let config = DockerConfig::get();
    let workspace_path = workspace_dir.canonicalize()
        .unwrap_or_else(|_| workspace_dir.to_path_buf());
    let workspace_mount = format!("{}:/workspace", workspace_path.display());

    let mut docker_args = vec![
        "run",
        "--rm",
        "--memory",
        &config.memory_limit,
        "--memory-swap",
        &config.memory_limit,
        "-v",
        &workspace_mount,
        "-w",
        "/workspace",
        OJT_DOCKER_IMAGE,
    ];
    docker_args.extend(args);

    let (stdout, stderr) = execute_program("docker", &docker_args.iter().map(|s| *s).collect::<Vec<&str>>().as_slice(), None).await?;
    Ok((stdout, stderr))
} 