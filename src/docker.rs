use std::path::{Path, PathBuf};
use std::time::Duration;
use std::process::Stdio;
use std::time::Instant;

use tokio::time::timeout;
use tokio::process::Command as TokioCommand;
use tokio::io::AsyncWriteExt;
use once_cell::sync::Lazy;

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
            Language::Rust => {
                let dir = "compile/rust";
                // compile/rustディレクトリを作成
                let absolute_path = std::env::current_dir()
                    .unwrap_or_else(|_| PathBuf::from("."))
                    .join(dir);
                let _ = std::fs::create_dir_all(&absolute_path.join("src"));
                
                // Cargo.tomlを作成
                let cargo_toml = r#"[package]
name = "compile"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "a"
path = "src/a.rs"
"#;
                let _ = std::fs::write(absolute_path.join("Cargo.toml"), cargo_toml);
                
                // パーミッションを設定
                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    let _ = std::fs::set_permissions(
                        absolute_path.join("Cargo.toml"),
                        std::fs::Permissions::from_mode(0o777)
                    );
                    let _ = std::fs::set_permissions(
                        &absolute_path,
                        std::fs::Permissions::from_mode(0o777)
                    );
                    let _ = std::fs::set_permissions(
                        absolute_path.join("src"),
                        std::fs::Permissions::from_mode(0o777)
                    );
                }
                
                dir
            },
            Language::PyPy => unreachable!(), // PyPyは別処理
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
            for line in input.lines() {
                stdin.write_all(line.as_bytes()).await
                    .map_err(|e| Error::Docker(DockerError::failed("write to stdin", e)))?;
                stdin.write_all(b"\n").await
                    .map_err(|e| Error::Docker(DockerError::failed("write to stdin", e)))?;
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
    image: String,
    cmd: &'a [&'a str],
    compile_mount: Option<String>,
}

impl<'a> DockerRunOptions<'a> {
    fn new_with_language(workspace_dir: &'a Path, language: &Language, cmd: &'a [&'a str], use_compile_dir: bool) -> Self {
        Self {
            workspace_dir,
            image: DockerConfig::get_image(language),
            cmd,
            compile_mount: if use_compile_dir {
                Some(match language {
                    Language::Rust => DockerConfig::get_compile_mount(language),
                    Language::PyPy => {
                        // PyPyの場合は、ソースファイルをmain.pyとしてマウント
                        let source_path = workspace_dir.join("a.py");  // 現在のソースファイル
                        let compile_dir = std::env::current_dir()
                            .unwrap_or_else(|_| PathBuf::from("."))
                            .join("compile/pypy");
                        
                        // compile/pypyディレクトリを作成
                        let _ = std::fs::create_dir_all(&compile_dir);
                        
                        // main.pyを作成またはコピー
                        if source_path.exists() {
                            let _ = std::fs::copy(&source_path, compile_dir.join("main.py"));
                            // パーミッションを設定
                            #[cfg(unix)]
                            {
                                use std::os::unix::fs::PermissionsExt;
                                let _ = std::fs::set_permissions(
                                    compile_dir.join("main.py"),
                                    std::fs::Permissions::from_mode(0o777)
                                );
                            }
                        }
                        
                        format!("{}:/compile", compile_dir.display())
                    }
                })
            } else {
                None
            },
        }
    }
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
        "-e".into(),
        "RUST_BACKTRACE=1".into(),
    ];

    if let Some(mount) = &opts.compile_mount {
        args.push("-v".into());
        args.push(mount.clone());
    }

    args.push("-v".into());
    args.push(workspace_mount);

    args.push("-w".into());
    if opts.compile_mount.is_some() {
        args.push("/compile".into());
    } else {
        args.push("/workspace".into());
    }

    args.push(opts.image.clone());
    args.extend(opts.cmd.iter().map(|s| (*s).into()));
    args
}

async fn run_docker_command(opts: &DockerRunOptions<'_>, stdin: Option<String>) -> Result<DockerOutput> {
    let args = get_docker_run_args(opts);
    let args: Vec<&str> = args.iter().map(AsRef::as_ref).collect();
    let mut child = TokioCommand::new("docker")
        .args(&args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| Error::Docker(DockerError::failed("spawn docker process", e)))?;

    if let Some(input) = stdin {
        if let Some(mut stdin) = child.stdin.take() {
            // 入力の各行を処理
            for line in input.lines() {
                stdin.write_all(line.as_bytes()).await
                    .map_err(|e| Error::Docker(DockerError::failed("write to stdin", e)))?;
                stdin.write_all(b"\n").await
                    .map_err(|e| Error::Docker(DockerError::failed("write to stdin", e)))?;
            }
            // 最後に明示的にflushして入力を確実に送信
            stdin.flush().await
                .map_err(|e| Error::Docker(DockerError::failed("flush stdin", e)))?;
        }
    }

    let start_time = Instant::now();
    let output = child.wait_with_output().await
        .map_err(|e| Error::Docker(DockerError::failed("wait for docker process", e)))?;
    let execution_time = start_time.elapsed();

    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();

    Ok(DockerOutput {
        stdout,
        stderr,
        execution_time,
    })
}

#[derive(Debug)]
pub struct DockerOutput {
    pub stdout: String,
    pub stderr: String,
    pub execution_time: std::time::Duration,
}

fn create_run_command(work_dir: &str, command: &str, stdin: &str) -> String {
    format!("cd {} && echo '{}' | {}", work_dir, stdin, command)
}

pub async fn run_in_docker(
    workspace_dir: &Path,
    language: &Language,
    args: &[&str],
    stdin: Option<String>,
) -> Result<DockerOutput> {
    match language {
        Language::Rust => {
            let source_file = args[0];
            let binary_name = Path::new(source_file)
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or(source_file);
            
            // ソースファイルをコピー
            let source_path = workspace_dir.join(source_file);
            let compile_dir = std::env::current_dir()
                .unwrap_or_else(|_| PathBuf::from("."))
                .join("compile/rust");
            if source_path.exists() {
                let _ = std::fs::copy(&source_path, compile_dir.join("src").join("a.rs"));
                // パーミッションを設定
                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    let _ = std::fs::set_permissions(
                        compile_dir.join("src").join("a.rs"),
                        std::fs::Permissions::from_mode(0o777)
                    );
                }
            }
            
            // まずコンパイル
            let compile_cmd = create_run_command(
                "/compile",
                &format!("cargo build --bin {}", binary_name),
                ""
            );
            let compile_cmd_slice = ["sh", "-c", &compile_cmd];
            let compile_opts = DockerRunOptions::new_with_language(
                workspace_dir,
                language,
                &compile_cmd_slice,
                true
            );

            let compile_result = run_docker_command(&compile_opts, None).await?;
            if compile_result.stderr.contains("error") {
                return Ok(compile_result);
            }

            // 次に実行
            let run_cmd = create_run_command(
                "/compile",
                &format!("/compile/target/debug/{}", binary_name),
                &stdin.unwrap_or_default()
            );
            let run_cmd_slice = ["sh", "-c", &run_cmd];
            let opts = DockerRunOptions::new_with_language(
                workspace_dir,
                language,
                &run_cmd_slice,
                true
            );

            run_docker_command(&opts, None).await
        },
        Language::PyPy => {
            let run_cmd = if args[0] == "sh" && args[1] == "-c" {
                // セットアップコマンドの場合
                args[2].to_string()
            } else {
                // 実行コマンドの場合
                if let Some(ref input) = stdin {
                    // 標準入力をファイルに書き出す
                    format!("cd /compile && echo '{}' > input.txt && pypy3 main.py < input.txt", input.replace("'", "'\"'\"'"))
                } else {
                    format!("cd /compile && pypy3 main.py")
                }
            };
            let run_cmd_slice = ["sh", "-c", &run_cmd];
            let opts = DockerRunOptions::new_with_language(
                workspace_dir,
                language,
                &run_cmd_slice,
                true
            );

            run_docker_command(&opts, None).await
        }
    }
}

// online judge tool用のDockerイメージ名
pub const OJT_DOCKER_IMAGE: &str = "cph-oj";

pub async fn run_oj_tool(
    workspace_dir: &Path,
    args: &[&str],
) -> Result<DockerOutput> {
    let opts = DockerRunOptions {
        workspace_dir,
        image: OJT_DOCKER_IMAGE.to_string(),
        cmd: args,
        compile_mount: None,
    };
    run_docker_command(&opts, None).await
} 