use thiserror::Error;
use crate::domain::errors::DomainError;
use crate::infrastructure::errors::InfrastructureError;

#[derive(Error, Debug)]
pub enum ApplicationError {
    #[error("Use case failed: {0}")]
    UseCaseFailed(String),
    
    #[error("Domain error: {0}")]
    Domain(#[from] DomainError),
    
    #[error("Infrastructure error: {0}")]
    Infrastructure(#[from] InfrastructureError),
    
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    
    #[error("Operation not permitted: {0}")]
    OperationNotPermitted(String),
    
    #[error("Resource conflict: {0}")]
    ResourceConflict(String),
}