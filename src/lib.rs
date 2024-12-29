pub mod cli;
pub mod config;
pub mod docker;
pub mod error;
pub mod test;
pub mod workspace;
pub mod oj;

pub use cli::Cli;

use std::fmt;
use std::str::FromStr;
use clap::ValueEnum;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize, ValueEnum)]
pub enum Language {
    #[clap(name = "rust", alias = "Rust", alias = "RUST")]
    Rust,
    #[clap(name = "pypy", alias = "py-py", alias = "PyPy", alias = "PYPY", alias = "Pypy")]
    PyPy,
}

impl fmt::Display for Language {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Language::Rust => write!(f, "rust"),
            Language::PyPy => write!(f, "pypy"),
        }
    }
}

impl FromStr for Language {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "rust" => Ok(Language::Rust),
            "pypy" | "py-py" | "pypy3" => Ok(Language::PyPy),
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

    pub fn get_id(&self, site: &cli::Site) -> &'static str {
        match (self, site) {
            (Language::Rust, cli::Site::AtCoder { .. }) => "5054",   // Rust (rustc 1.70.0)
            (Language::PyPy, cli::Site::AtCoder { .. }) => "5078",   // Python (PyPy 3.10-v7.3.12)
        }
    }

    pub fn default_content(&self) -> error::Result<String> {
        match self {
            Language::Rust => Ok(include_str!("templates/template/main.rs").to_string()),
            Language::PyPy => Ok(include_str!("templates/template/main.py").to_string()),
        }
    }
}
