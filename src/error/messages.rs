use serde::Deserialize;
use std::collections::HashMap;
use once_cell::sync::Lazy;

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

/// メッセージの種類
#[derive(Debug, Clone, Copy)]
pub enum MessageType {
    Error,
    Warning,
    Hint,
}

/// メッセージを取得します。
/// 
/// # Arguments
/// * `category` - メッセージのカテゴリ（"fs", "docker", "contest", "common"）
/// * `msg_type` - メッセージの種類（Error, Warning, Hint）
/// * `key` - メッセージのキー
/// 
/// # Returns
/// * `Option<&'static str>` - メッセージのテンプレート
pub fn get_message(category: &str, msg_type: MessageType, key: &str) -> Option<&'static str> {
    MESSAGES.messages.get(category).and_then(|cat| {
        match msg_type {
            MessageType::Error => cat.error.get(key),
            MessageType::Warning => cat.warning.get(key),
            MessageType::Hint => cat.hint.get(key),
        }
    }).map(|s| s.as_str())
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
pub fn format_message<D: std::fmt::Display>(
    category: &str,
    msg_type: MessageType,
    key: &str,
    args: D,
) -> String {
    let template = get_message(category, msg_type, key)
        .unwrap_or_else(|| panic!("メッセージが見つかりません: {}/{:?}/{}", category, msg_type, key));
    template.replace("{}", &args.to_string())
}

// 利便性のために各カテゴリのモジュールを提供
pub mod fs {
    use super::*;

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("fs", MessageType::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("fs", MessageType::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("fs", MessageType::Hint, key, args)
    }
}

pub mod docker {
    use super::*;

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("docker", MessageType::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("docker", MessageType::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("docker", MessageType::Hint, key, args)
    }
}

pub mod contest {
    use super::*;

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("contest", MessageType::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("contest", MessageType::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("contest", MessageType::Hint, key, args)
    }
}

pub mod common {
    use super::*;

    pub fn error<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("common", MessageType::Error, key, args)
    }

    pub fn warning<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("common", MessageType::Warning, key, args)
    }

    pub fn hint<D: std::fmt::Display>(key: &str, args: D) -> String {
        format_message("common", MessageType::Hint, key, args)
    }
} 