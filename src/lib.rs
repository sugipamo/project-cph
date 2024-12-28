pub mod cli;
pub mod docker;
pub mod error;
pub mod test;
pub mod workspace;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Language {
    Rust,
    PyPy,
}

impl Language {
    pub fn extension(&self) -> &'static str {
        match self {
            Language::Rust => "rs",
            Language::PyPy => "py",
        }
    }

    pub fn default_content(&self) -> crate::error::Result<String> {
        match self {
            Language::Rust => Ok(include_str!("templates/template/main.rs").to_string()),
            Language::PyPy => Ok(include_str!("templates/template/main.py").to_string()),
        }
    }
}
