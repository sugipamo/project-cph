use async_trait::async_trait;
use crate::docker::error::DockerResult;
use std::time::Duration;

#[async_trait]
pub trait ContainerManager: Send + Sync {
    async fn create_container(&mut self, image: &str, cmd: Vec<String>, working_dir: &str) -> DockerResult<()>;
    async fn start_container(&mut self) -> DockerResult<()>;
    async fn stop_container(&mut self) -> DockerResult<()>;
    async fn check_image(&self, image: &str) -> DockerResult<bool>;
    async fn pull_image(&self, image: &str) -> DockerResult<()>;
}

#[async_trait]
pub trait IOHandler: Send + Sync {
    async fn write(&self, input: &str) -> DockerResult<()>;
    async fn read_stdout(&self, timeout: Duration) -> DockerResult<String>;
    async fn read_stderr(&self, timeout: Duration) -> DockerResult<String>;
    async fn setup_io(&mut self) -> DockerResult<()>;
}

#[async_trait]
pub trait CompilationManager: Send + Sync {
    async fn compile(
        &mut self,
        source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> DockerResult<()>;
    
    async fn get_compilation_output(&self) -> DockerResult<(String, String)>;
}

#[async_trait]
pub trait DockerCommandExecutor: Send + Sync {
    /// Dockerコマンドを実行し、結果を返す
    /// 
    /// # 引数
    /// * `args` - Dockerコマンドの引数
    /// 
    /// # 戻り値
    /// * `DockerResult<(bool, String, String)>` - (成功したか, 標準出力, 標準エラー出力)
    async fn execute_command(&self, args: Vec<String>) -> DockerResult<(bool, String, String)>;
}

#[async_trait]
pub trait DockerRunner: Send + Sync {
    /// コンテナを初期化し、実行準備を行う
    async fn initialize(&mut self, cmd: Vec<String>) -> DockerResult<()>;

    /// コンテナに入力を送信する
    async fn write(&mut self, input: &str) -> DockerResult<()>;

    /// コンテナの標準出力を読み取る
    async fn read_stdout(&mut self) -> DockerResult<String>;

    /// コンテナの標準エラー出力を読み取る
    async fn read_stderr(&mut self) -> DockerResult<String>;

    /// コンテナを停止する
    async fn stop(&mut self) -> DockerResult<()>;
} 