use std::fmt;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use crate::docker::error::DockerError;

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerState {
    Initial,
    Running(ContainerContext),
    Completed(ExecutionResult),
    Failed(DockerError),
}

#[derive(Debug, Clone, PartialEq)]
pub struct ContainerContext {
    pub container_id: String,
    pub start_time: Instant,
    pub memory_usage: Option<u64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ExecutionResult {
    pub exit_code: i32,
    pub execution_time: Duration,
    pub output: String,
}

impl RunnerState {
    pub fn is_terminal(&self) -> bool {
        matches!(self, RunnerState::Completed(_) | RunnerState::Failed(_))
    }

    pub fn can_transition_to(&self, next: &RunnerState) -> bool {
        match (self, next) {
            (RunnerState::Initial, RunnerState::Running(_)) => true,
            (RunnerState::Running(_), RunnerState::Completed(_)) => true,
            (RunnerState::Running(_), RunnerState::Failed(_)) => true,
            _ => false,
        }
    }
} 