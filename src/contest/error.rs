use crate::error::Error;

pub use crate::error::contest::ContestErrorKind;

pub fn contest_error(kind: ContestErrorKind, message: impl Into<String>) -> Error {
    Error::new(kind, message)
}

pub fn not_found_error(message: impl Into<String>) -> Error {
    contest_error(ContestErrorKind::NotFound, message)
}

pub fn invalid_language_error(message: impl Into<String>) -> Error {
    contest_error(ContestErrorKind::InvalidLanguage, message)
}

pub fn invalid_url_error(message: impl Into<String>) -> Error {
    contest_error(ContestErrorKind::InvalidUrl, message)
}

pub fn parse_error(message: impl Into<String>) -> Error {
    contest_error(ContestErrorKind::Parse, message)
}
