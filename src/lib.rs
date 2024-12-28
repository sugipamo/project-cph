pub mod cli;
pub mod docker;
pub mod error;
pub mod test;
pub mod workspace;

use serde::{Deserialize, Serialize};
use clap::ValueEnum;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, ValueEnum)]
pub enum Language {
    #[clap(name = "rust")]
    Rust,
    #[clap(name = "py-py", alias = "pypy")]
    PyPy,
}

impl fmt::Display for Language {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Language::Rust => write!(f, "rust"),
            Language::PyPy => write!(f, "py-py"),
        }
    }
}

impl FromStr for Language {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "rust" => Ok(Language::Rust),
            "py-py" | "pypy" => Ok(Language::PyPy),
            _ => Err(format!("Unknown language: {}", s)),
        }
    }
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
