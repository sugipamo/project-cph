mod context;
mod app_error;

pub use app_error::{AppError, AppResult};

use thiserror::Error;
use crate::application::errors::ApplicationError;

#[derive(Error, Debug)]
pub enum CphError {
    #[error(transparent)]
    Application(#[from] ApplicationError),
    
    #[error("CLI error: {0}")]
    Cli(String),
    
    #[error("Unknown error: {0}")]
    Unknown(String),
}

pub type Result<T> = std::result::Result<T, CphError>;

impl CphError {
    /// Convert error to user-friendly message
    pub fn to_user_message(&self) -> String {
        match self {
            CphError::Application(app_err) => match app_err {
                ApplicationError::InvalidInput(msg) => format!("Invalid input: {}", msg),
                ApplicationError::OperationNotPermitted(msg) => format!("Operation not permitted: {}", msg),
                ApplicationError::ResourceConflict(msg) => format!("Resource conflict: {}", msg),
                _ => format!("An error occurred: {}", app_err),
            },
            CphError::Cli(msg) => format!("Command line error: {}", msg),
            CphError::Unknown(msg) => format!("An unexpected error occurred: {}", msg),
        }
    }
    
    /// Get suggested action for the error
    pub fn suggested_action(&self) -> Option<String> {
        match self {
            CphError::Application(ApplicationError::InvalidInput(_)) => 
                Some("Please check your input and try again.".to_string()),
            CphError::Application(ApplicationError::OperationNotPermitted(_)) => 
                Some("Please check your permissions or contact an administrator.".to_string()),
            CphError::Application(ApplicationError::ResourceConflict(_)) => 
                Some("Please try again later or resolve the conflict.".to_string()),
            _ => None,
        }
    }
}