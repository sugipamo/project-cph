pub mod error;
pub mod fs;

use crate::config::Config;
use error::{Result, ContestError};
use std::sync::Arc;
use std::path::{Path, PathBuf};

pub mod core;
