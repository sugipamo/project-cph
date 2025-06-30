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
        *self.level.lock().unwrap() = level;
        // Note: In a real implementation, we'd need to update the tracing subscriber
    }
}