pub mod cli;
pub mod docker;
pub mod error;
pub mod workspace;

use std::fmt;
use std::path::Path;
use crate::error::Result;

const DEFAULT_TIMEOUT_SECS: u64 = 2;
const DEFAULT_MEMORY_LIMIT: &str = "256m";

#[derive(Debug, Clone, Copy, clap::ValueEnum)]
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
        Ok(match self {
            Language::Rust => include_str!("templates/template/main.rs").to_string(),
            Language::PyPy => include_str!("templates/template/main.py").to_string(),
        })
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
