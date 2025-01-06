use std::time::Duration;

#[derive(Clone, Debug)]
pub struct ContainerConfig {
    pub image: String,
    pub memory_limit: u64,
    pub working_dir: String,
    pub mount_point: String,
    pub timeout: Option<Duration>,
}

impl ContainerConfig {
    pub fn new(
        image: String,
        memory_limit: u64,
        working_dir: String,
        mount_point: String,
    ) -> Self {
        Self {
            image,
            memory_limit,
            working_dir,
            mount_point,
            timeout: None,
        }
    }

    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }

    pub fn into_create_args(self) -> Vec<String> {
        vec![
            "create".to_string(),
            "-i".to_string(),
            "--rm".to_string(),
            "-m".to_string(),
            format!("{}m", self.memory_limit),
            "-v".to_string(),
            format!("{}:{}", self.mount_point, self.working_dir),
            "-w".to_string(),
            self.working_dir,
            self.image,
        ]
    }
} 