use std::fmt;
use crate::docker::error::{DockerError, Result};

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerState {
    Ready,
    Running,
    Stop,
    Error,
}

impl fmt::Display for RunnerState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RunnerState::Ready => write!(f, "Ready"),
            RunnerState::Running => write!(f, "Running"),
            RunnerState::Stop => write!(f, "Stop"),
            RunnerState::Error => write!(f, "Error"),
        }
    }
}

impl RunnerState {
    pub fn can_transition_to(&self, next: &RunnerState) -> Result<()> {
        match (self, next) {
            (RunnerState::Ready, RunnerState::Running) => Ok(()),
            (RunnerState::Running, RunnerState::Stop) => Ok(()),
            (RunnerState::Running, RunnerState::Error) => Ok(()),
            (from, to) => Err(DockerError::InvalidStateTransition {
                from: from.to_string(),
                to: to.to_string(),
            }),
        }
    }
} 