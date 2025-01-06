use async_trait::async_trait;
use std::time::Duration;
use crate::docker::error::DockerResult;
use crate::docker::config::ContainerConfig;

#[async_trait]
pub trait DockerOperations: Send + Sync {
    /// コンテナを作成し、初期化する
    async fn initialize(&mut self, config: ContainerConfig) -> DockerResult<()>;

    /// コンテナを起動する
    async fn start(&mut self) -> DockerResult<()>;

    /// コンテナを停止する
    async fn stop(&mut self) -> DockerResult<()>;

    /// コンテナにコマンドを実行する
    async fn execute(&mut self, command: &str) -> DockerResult<(String, String)>;

    /// コンテナの標準入力にデータを書き込む
    async fn write(&mut self, input: &str) -> DockerResult<()>;

    /// コンテナの標準出力からデータを読み取る
    async fn read_stdout(&mut self, timeout: Duration) -> DockerResult<String>;

    /// コンテナの標準エラー出力からデータを読み取る
    async fn read_stderr(&mut self, timeout: Duration) -> DockerResult<String>;
}

#[async_trait]
pub trait CompilationOperations: Send + Sync {
    /// ソースコードをコンパイルする
    async fn compile(
        &mut self,
        source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> DockerResult<()>;

    /// コンパイル結果を取得する
    async fn get_compilation_output(&self) -> DockerResult<(String, String)>;
} 