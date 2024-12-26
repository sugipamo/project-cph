pub mod cli;
pub mod docker;
pub mod error;
pub mod workspace;

use std::fmt;
use std::path::Path;
use crate::error::Result;

const DEFAULT_TIMEOUT_SECS: u64 = 30;
const DEFAULT_MEMORY_LIMIT: &str = "256m";

#[derive(Debug, Clone, Copy, clap::ValueEnum, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Language {
    Rust,
    PyPy,
}

impl Language {
    pub fn docker_image(&self) -> &'static str {
        match self {
            Language::Rust => "rust:1.70",
            Language::PyPy => "pypy:3",
        }
    }

    pub fn extension(&self) -> &str {
        match self {
            Language::Rust => "rs",
            Language::PyPy => "py",
        }
    }

    pub fn default_content(&self) -> Result<String> {
        let template_path = Path::new("src/templates/template").join(match self {
            Language::Rust => "main.rs",
            Language::PyPy => "main.py",
        });

        if template_path.exists() {
            Ok(std::fs::read_to_string(template_path)?)
        } else {
            // テンプレートファイルが見つからない場合のデフォルト内容
            Ok(match self {
                Language::Rust => "fn main() {\n    println!(\"Hello, World!\");\n}\n".to_string(),
                Language::PyPy => "print('Hello, World!')\n".to_string(),
            })
        }
    }
}

impl fmt::Display for Language {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Language::Rust => write!(f, "rust"),
            Language::PyPy => write!(f, "pypy"),
        }
    }
}
