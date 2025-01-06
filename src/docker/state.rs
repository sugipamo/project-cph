use std::fmt;
use std::collections::HashMap;
use std::time::{Duration, Instant};

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerStatus {
    Ready,
    Running,
    Error(String),
    Stop,
    Completed,
}

impl fmt::Display for RunnerStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RunnerStatus::Error(msg) => write!(f, "Error: {}", msg),
            _ => write!(f, "{:?}", self),
        }
    }
}

pub struct RunnerState {
    status: RunnerStatus,
    start_time: Option<Instant>,
    execution_time: Option<Duration>,
    runner_statuses: HashMap<usize, RunnerStatus>,
}

impl RunnerState {
    pub fn new() -> Self {
        Self {
            status: RunnerStatus::Ready,
            start_time: None,
            execution_time: None,
            runner_statuses: HashMap::new(),
        }
    }

    pub fn start(&mut self) {
        self.status = RunnerStatus::Running;
        self.start_time = Some(Instant::now());
    }

    pub fn stop(&mut self) {
        self.status = RunnerStatus::Stop;
        self.set_execution_time();
    }

    pub fn error(&mut self, message: String) {
        self.status = RunnerStatus::Error(message);
        self.set_execution_time();
    }

    pub fn complete(&mut self) {
        self.status = RunnerStatus::Completed;
        self.set_execution_time();
    }

    fn set_execution_time(&mut self) {
        if let Some(start) = self.start_time {
            self.execution_time = Some(start.elapsed());
        }
    }

    pub fn update_runner(&mut self, id: usize, status: RunnerStatus) -> Result<(), String> {
        self.runner_statuses.insert(id, status.clone());
        
        // 全体の状態を更新
        self.status = match status {
            RunnerStatus::Error(msg) => RunnerStatus::Error(msg),
            RunnerStatus::Stop if self.all_runners_stopped() => RunnerStatus::Stop,
            RunnerStatus::Completed if self.all_runners_completed() => RunnerStatus::Completed,
            _ => self.status.clone(),
        };

        Ok(())
    }

    pub fn get_runner_status(&self, id: usize) -> Option<&RunnerStatus> {
        self.runner_statuses.get(&id)
    }

    pub fn get_status(&self) -> &RunnerStatus {
        &self.status
    }

    pub fn get_execution_time(&self) -> Option<Duration> {
        self.execution_time
    }

    fn all_runners_stopped(&self) -> bool {
        !self.runner_statuses.is_empty() && self.runner_statuses.values()
            .all(|s| matches!(s, RunnerStatus::Stop | RunnerStatus::Completed))
    }

    fn all_runners_completed(&self) -> bool {
        !self.runner_statuses.is_empty() && self.runner_statuses.values()
            .all(|s| matches!(s, RunnerStatus::Completed))
    }

    pub fn can_transition_to(&self, next: &RunnerStatus) -> bool {
        match (&self.status, next) {
            (RunnerStatus::Ready, RunnerStatus::Running) => true,
            (RunnerStatus::Running, RunnerStatus::Stop) => true,
            (RunnerStatus::Running, RunnerStatus::Error(_)) => true,
            (RunnerStatus::Running, RunnerStatus::Completed) => true,
            (RunnerStatus::Error(_), RunnerStatus::Stop) => true,
            _ => false
        }
    }
} 