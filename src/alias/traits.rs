use std::error::Error;

/// エイリアス解決のための結果型
pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

/// エイリアス解決を行うトレイト
pub trait AliasResolver {
    /// 入力文字列からエイリアスを解決する
    fn resolve(&self, input: &str) -> Result<String>;

    /// 解決された値が有効かどうかを検証する
    fn validate(&self, resolved: &str) -> Result<()>;

    /// このリゾルバーが処理できるカテゴリを返す
    fn category(&self) -> &str;
}
