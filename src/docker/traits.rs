/*
TODO: リファクタリング計画 - トレイトの分割と整理

このファイルは将来的に以下のような構造に分割することを検討:

src/docker/traits/
├── mod.rs          - トレイトモジュールのエントリーポイント
├── container.rs    - ContainerManagerトレイト
├── operations.rs   - DockerOperationsトレイト
└── compilation.rs  - CompilationOperationsトレイト

目的:
- 各トレイトの責務をより明確に分離
- テスタビリティの向上
- コードの保守性と可読性の向上
*/

use async_trait::async_trait;
use std::time::Duration;
use crate::docker::error::DockerResult;
use crate::docker::config::ContainerConfig;

#[async_trait]
pub trait ContainerManager: Send + Sync {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
    async fn start_container(&mut self) -> DockerResult<()>;
    async fn stop_container(&mut self) -> DockerResult<()>;
    async fn get_container_id(&self) -> DockerResult<String>;
    async fn get_exit_code(&self) -> DockerResult<i32>;
    async fn check_image(&self, image: &str) -> DockerResult<bool>;
    async fn pull_image(&self, image: &str) -> DockerResult<()>;
}

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