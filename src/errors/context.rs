use std::fmt::Display;

/// Extension trait for adding context to errors
#[allow(dead_code)]
pub trait ErrorContext<T> {
    /// Add context to the error
    fn context<C>(self, context: C) -> Result<T, anyhow::Error>
    where
        C: Display + Send + Sync + 'static;
    
    /// Add context with a closure that's only evaluated on error
    fn with_context<C, F>(self, context: F) -> Result<T, anyhow::Error>
    where
        C: Display + Send + Sync + 'static,
        F: FnOnce() -> C;
}

impl<T, E> ErrorContext<T> for Result<T, E>
where
    E: std::error::Error + Send + Sync + 'static,
{
    fn context<C>(self, context: C) -> Result<T, anyhow::Error>
    where
        C: Display + Send + Sync + 'static,
    {
        self.map_err(|e| anyhow::anyhow!(e).context(context))
    }
    
    fn with_context<C, F>(self, context: F) -> Result<T, anyhow::Error>
    where
        C: Display + Send + Sync + 'static,
        F: FnOnce() -> C,
    {
        self.map_err(|e| anyhow::anyhow!(e).context(context()))
    }
}