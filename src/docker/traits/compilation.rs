use async_trait::async_trait;
use crate::docker::error::DockerResult;

/// コンパイル関連操作を提供するトレイト
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