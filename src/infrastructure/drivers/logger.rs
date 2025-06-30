use crate::interfaces::logger::{Logger, LogLevel};
use std::sync::Mutex;

pub struct TracingLogger {
    level: Mutex<LogLevel>,
}

impl TracingLogger {
    pub fn new() -> Self {
        Self {
            level: Mutex::new(LogLevel::Info),
        }
    }
}

impl Logger for TracingLogger {
    fn trace(&self, message: &str) {
        tracing::trace!("{}", message);
    }

    fn debug(&self, message: &str) {
        tracing::debug!("{}", message);
    }

    fn info(&self, message: &str) {
        tracing::info!("{}", message);
    }

    fn warn(&self, message: &str) {
        tracing::warn!("{}", message);
    }

    fn error(&self, message: &str) {
        tracing::error!("{}", message);
    }

    fn set_level(&self, level: LogLevel) {
        match self.level.lock() {
            Ok(mut guard) => *guard = level,
            Err(poisoned) => {
                // If the mutex is poisoned, we can still recover by ignoring the poison
                let mut guard = poisoned.into_inner();
                *guard = level;
            }
        }
        // Note: In a real implementation, we'd need to update the tracing subscriber
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tracing_logger_creation() {
        let logger = TracingLogger::new();
        // Logger should be created successfully
        logger.info("Test logger created");
    }

    #[test]
    fn test_set_level() {
        let logger = TracingLogger::new();
        logger.set_level(LogLevel::Debug);
        // Level should be updated (though we can't easily verify tracing output in tests)
    }
}