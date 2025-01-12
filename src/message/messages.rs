use std::collections::HashMap;
use once_cell::sync::Lazy;
use colored::*;
use anyhow::{Result, anyhow};

#[derive(Debug, Clone, Copy)]
pub enum Type {
    Error,
    Warning,
    Hint,
}

static MESSAGES: Lazy<HashMap<&'static str, HashMap<&'static str, &'static str>>> = Lazy::new(|| {
    let mut m = HashMap::new();
    
    // ファイルシステム関連のメッセージ
    let mut fs = HashMap::new();
    fs.insert("file_not_found", "ファイルが見つかりません: {}");
    fs.insert("dir_not_found", "ディレクトリが見つかりません: {}");
    fs.insert("permission_denied", "アクセス権限がありません: {}");
    m.insert("fs", fs);

    // コンテナ関連のメッセージ
    let mut container = HashMap::new();
    container.insert("image_not_found", "イメージが見つかりません: {}");
    container.insert("container_error", "コンテナの操作に失敗しました: {}");
    container.insert("runtime_error", "ランタイムエラーが発生しました: {}");
    m.insert("container", container);

    // コンテスト関連のメッセージ
    let mut contest = HashMap::new();
    contest.insert("not_found", "コンテストが見つかりません: {}");
    contest.insert("invalid_format", "コンテスト形式が無効です: {}");
    m.insert("contest", contest);

    // 共通メッセージ
    let mut common = HashMap::new();
    common.insert("unknown_error", "不明なエラーが発生しました: {}");
    common.insert("invalid_argument", "無効な引数です: {}");
    m.insert("common", common);

    m
});

/// メッセージをフォーマットします。
///
/// # Arguments
/// * `category` - メッセージのカテゴリ（"fs", "container", "contest", "common"）
/// * `type_` - メッセージの種類
/// * `key` - メッセージのキー
/// * `arg` - フォーマット引数
///
/// # Returns
/// フォーマットされたメッセージ
fn format(category: &str, type_: Type, key: &str, arg: impl std::fmt::Display) -> String {
    let messages = MESSAGES.get(category).unwrap_or_else(|| MESSAGES.get("common").unwrap());
    let template = messages.get(key).unwrap_or_else(|| messages.get("unknown_error").unwrap());
    
    let formatted = template.replace("{}", &arg.to_string());

    match type_ {
        Type::Error => formatted.red().to_string(),
        Type::Warning => formatted.yellow().to_string(),
        Type::Hint => formatted.cyan().to_string(),
    }
}

pub mod fs {
    use super::{format, Type};

    pub fn error(key: &str, arg: impl std::fmt::Display) -> String {
        format("fs", Type::Error, key, arg)
    }

    pub fn warning(key: &str, arg: impl std::fmt::Display) -> String {
        format("fs", Type::Warning, key, arg)
    }

    pub fn hint(key: &str, arg: impl std::fmt::Display) -> String {
        format("fs", Type::Hint, key, arg)
    }
}

pub mod container {
    use super::{format, Type};

    pub fn error(key: &str, arg: impl std::fmt::Display) -> String {
        format("container", Type::Error, key, arg)
    }

    pub fn warning(key: &str, arg: impl std::fmt::Display) -> String {
        format("container", Type::Warning, key, arg)
    }

    pub fn hint(key: &str, arg: impl std::fmt::Display) -> String {
        format("container", Type::Hint, key, arg)
    }
}

pub mod contest {
    use super::{format, Type};

    pub fn error(key: &str, arg: impl std::fmt::Display) -> String {
        format("contest", Type::Error, key, arg)
    }

    pub fn warning(key: &str, arg: impl std::fmt::Display) -> String {
        format("contest", Type::Warning, key, arg)
    }

    pub fn hint(key: &str, arg: impl std::fmt::Display) -> String {
        format("contest", Type::Hint, key, arg)
    }
}

pub mod common {
    use super::{format, Type};

    pub fn error(key: &str, arg: impl std::fmt::Display) -> String {
        format("common", Type::Error, key, arg)
    }
} 