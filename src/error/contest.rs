use anyhow::{Error, Context as _};

pub fn contest_error(message: impl Into<String>) -> Error {
    Error::msg(message.into())
}

pub fn with_context<T, E>(result: Result<T, E>, message: impl Into<String>) -> Result<T, Error>
where
    E: std::error::Error + Send + Sync + 'static,
{
    result.with_context(|| message.into())
} 