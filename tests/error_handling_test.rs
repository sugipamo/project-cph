use cph::errors::{CphError, ErrorContext};
use cph::application::errors::ApplicationError;
use cph::domain::errors::DomainError;
use cph::infrastructure::errors::InfrastructureError;

#[test]
fn test_error_conversion() {
    // Test domain error to application error conversion
    let domain_err = DomainError::ProblemNotFound("test_problem".to_string());
    let app_err: ApplicationError = domain_err.into();
    matches!(app_err, ApplicationError::Domain(_));

    // Test application error to cph error conversion
    let cph_err: CphError = app_err.into();
    matches!(cph_err, CphError::Application(_));
}

#[test]
fn test_user_friendly_messages() {
    let err = CphError::Application(ApplicationError::InvalidInput("test input".to_string()));
    assert_eq!(err.to_user_message(), "Invalid input: test input");
    assert_eq!(
        err.suggested_action(),
        Some("Please check your input and try again.".to_string())
    );
}

#[test]
fn test_error_context() {
    use std::fs;
    
    let result = fs::read_to_string("/nonexistent/file")
        .context("Failed to read configuration file");
    
    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(err.to_string().contains("Failed to read configuration file"));
}

#[test]
fn test_infrastructure_error_conversion() {
    use std::io;
    
    let io_err = io::Error::new(io::ErrorKind::NotFound, "File not found");
    let infra_err: InfrastructureError = io_err.into();
    matches!(infra_err, InfrastructureError::FileSystem(_));
}