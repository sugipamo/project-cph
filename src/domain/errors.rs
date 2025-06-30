use thiserror::Error;

#[derive(Error, Debug)]
pub enum DomainError {
    #[error("Problem not found: {0}")]
    ProblemNotFound(String),
    
    #[error("Invalid test case: {message}")]
    InvalidTestCase { message: String },
    
    #[error("Invalid configuration: {0}")]
    InvalidConfiguration(String),
    
    #[error("Workflow execution failed: {0}")]
    WorkflowExecutionFailed(String),
    
    #[error("Validation error: {0}")]
    ValidationError(String),
}