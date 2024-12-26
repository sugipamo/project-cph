use std::path::Path;
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

// Dockerコンテナの実行オプション
struct DockerRunOptions<'a> {
    workspace_dir: &'a Path,
    image: &'a str,
    cmd: &'a [&'a str],
    compile_mount: Option<String>,
}

// Dockerコマンドの共通実行ロジック
fn get_docker_run_args(opts: &DockerRunOptions) -> Vec<String> {
    let config = DockerConfig::get();
    let workspace_path = opts.workspace_dir.canonicalize()
        .unwrap_or_else(|_| opts.workspace_dir.to_path_buf());
    let workspace_mount = format!("{}:/workspace", workspace_path.display());

    let mut args = vec![
        "run".into(),
        "--rm".into(),
        "--memory".into(),
        config.memory_limit.clone(),
        "--memory-swap".into(),
        config.memory_limit.clone(),
        "-v".into(),
        workspace_mount,
        "-w".into(),
        "/workspace".into(),
    ];

    if let Some(mount) = &opts.compile_mount {
        args.push("-v".into());
        args.push(mount.clone());
    }

    args.push(opts.image.into());
    args.extend(opts.cmd.iter().map(|s| (*s).into()));
    args
}

pub async fn run_in_docker(
    workspace_dir: &Path,
    language: &Language,
    cmd: &[&str],
) -> Result<(String, String)> {
    let opts = DockerRunOptions {
        workspace_dir,
        image: &DockerConfig::get_image(language),
        cmd,
        compile_mount: Some(DockerConfig::get_compile_mount(language)),
    };

    let args = get_docker_run_args(&opts);
    let args: Vec<&str> = args.iter().map(AsRef::as_ref).collect();
    execute_program("docker", &args, None).await
}

// online judge tool用のDockerイメージ名
pub const OJT_DOCKER_IMAGE: &str = "cph-oj";

pub async fn run_oj_tool(
    workspace_dir: &Path,
    args: &[&str],
) -> Result<(String, String)> {
    let opts = DockerRunOptions {
        workspace_dir,
        image: OJT_DOCKER_IMAGE,
        cmd: args,
        compile_mount: None,
    };

    let args = get_docker_run_args(&opts);
    let args: Vec<&str> = args.iter().map(AsRef::as_ref).collect();
    execute_program("docker", &args, None).await
} 