use serde::Deserialize;
use std::collections::HashMap;
use once_cell::sync::Lazy;
use super::Type;

#[derive(Debug, Deserialize)]
struct MessageCategory {
    error: HashMap<String, String>,
    warning: HashMap<String, String>,
    hint: HashMap<String, String>,
}

#[derive(Debug, Deserialize)]
struct Messages {
    messages: HashMap<String, MessageCategory>,
}

static MESSAGES: Lazy<Messages> = Lazy::new(|| {
    let yaml = include_str!("messages.yaml");
    serde_yaml::from_str(yaml).expect("メッセージ定義の読み込みに失敗しました")
});

/// メッセージを取得します。
/// 
/// # Arguments
/// * `category` - メッセージのカテゴリ（"fs", "docker", "contest", "common"）
/// * `msg_type` - メッセージの種類（Error, Warning, Hint）
/// * `key` - メッセージのキー
/// 
/// # Returns
/// * `Option<&'static str>` - メッセージのテンプレート
#[must_use]
pub fn get(category: &str, msg_type: Type, key: &str) -> Option<&'static str> {
    MESSAGES.messages.get(category).and_then(|cat| {
        match msg_type {
            Type::Error => cat.error.get(key),
            Type::Warning => cat.warning.get(key),
            Type::Hint => cat.hint.get(key),
        }
    }).map(String::as_str)
}

/// メッセージをフォーマットします。
/// 
/// # Arguments
/// * `category` - メッセージのカテゴリ
/// * `msg_type` - メッセージの種類
/// * `key` - メッセージのキー
/// * `args` - フォーマット引数
/// 
/// # Returns
/// * `String` - フォーマットされたメッセージ
/// 
/// # Panics
/// * メッセージが見つからない場合
pub fn format<D: std::fmt::Display>(
    category: &str,
    msg_type: Type,
    key: &str,
    args: D,
) -> String {
    let template = get(category, msg_type, key)
        .unwrap_or_else(|| panic!("メッセージが見つかりません: {category}/{msg_type:?}/{key}"));
    template.replace("{}", &args.to_string())
}

// 利便性のために各カテゴリのモジュールを提供
pub mod fs {
    use super::{Type, format};

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("fs", Type::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("fs", Type::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("fs", Type::Hint, key, args)
    }
}

pub mod docker {
    use super::{Type, format};

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("docker", Type::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("docker", Type::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("docker", Type::Hint, key, args)
    }
}

pub mod contest {
    use super::{Type, format};

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("contest", Type::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("contest", Type::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("contest", Type::Hint, key, args)
    }
}

pub mod common {
    use super::{Type, format};

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("common", Type::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("common", Type::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format("common", Type::Hint, key, args)
    }
} 