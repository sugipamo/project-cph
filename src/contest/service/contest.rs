use crate::config::Config;
use crate::docker::DockerRunner;
use crate::contest::error::{ContestError, ContestResult};
use crate::docker::traits::{ContainerManager, IOHandler, CompilationManager};
use crate::docker::runner::default_impl::{DefaultContainerManager, DefaultIOHandler, DefaultCompilationManager};

pub struct ContestService {
    config: Config,
}

impl ContestService {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub async fn run_test(&self, source_code: &str) -> ContestResult<String> {
        let config = self.config.clone();
        let memory_limit = config.get_memory_limit()
            .map_err(|e| ContestError::Config(e.to_string()))?;
        let mount_point = config.get_mount_point()
            .map_err(|e| ContestError::Config(e.to_string()))?;
        let working_dir = config.get_working_dir()
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let container_manager = Box::new(DefaultContainerManager::new(
            memory_limit,
            mount_point,
        ));
        let io_handler = Box::new(DefaultIOHandler::new(String::new()));
        let compilation_manager = Box::new(DefaultCompilationManager::new(
            String::new(),
            working_dir,
        ));

        let mut docker_runner = DockerRunner::new(
            config,
            container_manager,
            io_handler,
            compilation_manager,
        );

        docker_runner.run_in_docker(source_code)
            .await
            .map_err(|e| ContestError::Contest(e.to_string()))
    }
} 