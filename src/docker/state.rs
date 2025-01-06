use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum RunnerState {
    Ready,
    Running,
    Error,
    Stop,
    Completed,
}

impl fmt::Display for RunnerState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl RunnerState {
    pub fn can_transition_to(&self, next: &RunnerState) -> bool {
        match (self, next) {
            (RunnerState::Ready, RunnerState::Running) => true,
            (RunnerState::Running, RunnerState::Stop) => true,
            (RunnerState::Running, RunnerState::Error) => true,
            (RunnerState::Error, RunnerState::Stop) => true,
            _ => {
                println!("Invalid state transition from {:?} to {:?}", self, next);
                false
            }
        }
    }
} 