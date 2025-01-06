#[cfg(test)]
mod tests {
    use super::*;
}

pub mod config;
pub mod docker;
pub mod contest;
pub mod fs;
pub mod test;
pub mod error;

pub use config::Config;
pub use contest::ContestService;
pub use error::{CphError, Result};
