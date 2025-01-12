use anyhow::Result;
use tokio::io::AsyncReadExt;
use std::sync::Arc;
use tokio::sync::Mutex;
use containerd_client::services::v1::WaitRequest;
use tracing;
use nix::unistd::pipe;

use super::image::ContainerdBuilder;

/// コマンド実行時のバッファ設定
#[derive(Debug, Clone, Copy)]
pub struct BufferConfig {
    /// バッファサイズ（バイト）
    pub buffer_size: usize,
    /// 出力をリアルタイムでログに記録するかどうか
    pub stream_output: bool,
}

impl Default for BufferConfig {
    fn default() -> Self {
        Self {
            buffer_size: 1024 * 64, // 64KB
            stream_output: true,
        }
    }
}

/// コマンド実行の出力を格納する構造体
#[derive(Debug, Clone)]
pub struct CommandOutput {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

impl ContainerdBuilder {
    pub async fn execute_command(&self, container_id: &str, command: &[String]) -> Result<CommandOutput> {
        let mut tasks = self.tasks.lock().await;
        let exec_id = uuid::Uuid::new_v4().to_string();
        let buffer_config = BufferConfig::default();

        // 環境変数の取得
        let default_lang: String = self.config.get("languages.default")?;
        let env_vars: Vec<String> = self.config.get(&format!("languages.{}.container.env_vars", default_lang))
            .unwrap_or_default();

        // 出力バッファの準備
        let stdout_buf = Arc::new(Mutex::new(Vec::new()));
        let stderr_buf = Arc::new(Mutex::new(Vec::new()));

        // プロセス仕様の作成
        let process_spec = serde_json::json!({
            "terminal": false,
            "args": command,
            "env": env_vars,
            "cwd": "/",
            "capabilities": {
                "bounding": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "effective": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "inheritable": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "permitted": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ],
                "ambient": [
                    "CAP_AUDIT_WRITE",
                    "CAP_KILL",
                    "CAP_NET_BIND_SERVICE"
                ]
            },
            "rlimits": [
                {
                    "type": "RLIMIT_NOFILE",
                    "hard": 1024,
                    "soft": 1024
                }
            ],
            "noNewPrivileges": true
        });

        // 標準出力と標準エラー出力のパイプを作成
        let (stdout_reader, _) = tokio::io::duplex(buffer_config.buffer_size);
        let (stderr_reader, _) = tokio::io::duplex(buffer_config.buffer_size);

        // パイプの作成
        let (_, stdout_write_fd) = pipe()?;
        let (_, stderr_write_fd) = pipe()?;

        // Execの作成と実行
        let _exec = tasks.exec(containerd_client::services::v1::ExecProcessRequest {
            container_id: container_id.to_string(),
            exec_id: exec_id.clone(),
            terminal: false,
            stdin: String::new(),
            stdout: stdout_write_fd.to_string(),
            stderr: stderr_write_fd.to_string(),
            spec: Some(prost_types::Any {
                type_url: "types.containerd.io/opencontainers/runtime-spec/1/Process".to_string(),
                value: serde_json::to_vec(&process_spec)?,
            }),
        })
        .await?;

        // 出力の読み取り処理
        let stdout_buf_clone = Arc::clone(&stdout_buf);
        let stderr_buf_clone = Arc::clone(&stderr_buf);
        let stream_output = buffer_config.stream_output;
        let cmd_str = Arc::new(command.join(" "));

        let stdout_handle = {
            let cmd_str = Arc::clone(&cmd_str);
            tokio::spawn(async move {
                let mut reader = tokio::io::BufReader::new(stdout_reader);
                let mut buffer = vec![0u8; buffer_config.buffer_size];
                while let Ok(n) = reader.read(&mut buffer).await {
                    if n == 0 {
                        break;
                    }
                    if stream_output {
                        let output = String::from_utf8_lossy(&buffer[..n]).to_string();
                        tracing::debug!("[{}] stdout: {}", cmd_str, output);
                    }
                    stdout_buf_clone.lock().await.extend_from_slice(&buffer[..n]);
                }
            })
        };

        let stderr_handle = {
            let cmd_str = Arc::clone(&cmd_str);
            tokio::spawn(async move {
                let mut reader = tokio::io::BufReader::new(stderr_reader);
                let mut buffer = vec![0u8; buffer_config.buffer_size];
                while let Ok(n) = reader.read(&mut buffer).await {
                    if n == 0 {
                        break;
                    }
                    if stream_output {
                        let output = String::from_utf8_lossy(&buffer[..n]).to_string();
                        tracing::debug!("[{}] stderr: {}", cmd_str, output);
                    }
                    stderr_buf_clone.lock().await.extend_from_slice(&buffer[..n]);
                }
            })
        };

        // 実行結果の待機
        let status = tasks.wait(WaitRequest {
            container_id: container_id.to_string(),
            exec_id: exec_id.clone(),
        })
        .await?
        .into_inner()
        .exit_status;

        // 出力の読み取り完了を待機
        tokio::try_join!(stdout_handle, stderr_handle)?;

        // 出力の取得
        let stdout = String::from_utf8(stdout_buf.lock().await.clone())?;
        let stderr = String::from_utf8(stderr_buf.lock().await.clone())?;

        if status != 0 {
            return Err(anyhow::anyhow!(
                "コマンドの実行に失敗しました: {:?} (exit code: {})\nstderr: {}",
                command,
                status,
                stderr
            ));
        }

        Ok(CommandOutput {
            stdout,
            stderr,
            exit_code: status as i32,
        })
    }
} 