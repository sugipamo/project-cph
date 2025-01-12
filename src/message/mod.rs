pub mod messages;

/// メッセージの種類
#[derive(Debug, Clone, Copy)]
pub enum Type {
    Error,
    Warning,
    Hint,
}

pub use messages::{get, format};
pub use messages::{fs, container, contest, common}; 