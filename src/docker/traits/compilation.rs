use async_trait::async_trait;
use anyhow::Result;

/// コンパイル操作を提供するトレイト
///
/// このトレイトは、ソースコードのコンパイルに関連する
/// 基本的な操作を定義します。
#[async_trait]
pub trait CompilerOperations: Send + Sync {
    /// ソースコードをコンパイルします
    ///
    /// # Arguments
    /// * `source_code` - コンパイル対象のソースコード
    /// * `compile_cmd` - コンパイルコマンドとその引数（オプション）
    /// * `env_vars` - コンパイル時に設定する環境変数
    ///
    /// # Returns
    /// * `Result<()>` - コンパイル結果
    ///
    /// # Errors
    /// * コンパイルに失敗した場合
    /// * コンパイラの実行に失敗した場合
    async fn compile(
        &mut self,
        source_code: &str,
        compile_cmd: Option<Vec<String>>,
        env_vars: Vec<String>,
    ) -> Result<()>;

    /// コンパイル結果を取得します
    ///
    /// # Returns
    /// * `Result<(String, String)>` - (標準出力, 標準エラー出力)
    ///
    /// # Errors
    /// * コンパイル結果の取得に失敗した場合
    async fn get_compilation_output(&self) -> Result<(String, String)>;
} 