use crate::config::Config;
use crate::docker::DockerRunner;
use crate::contest::error::Result;

pub struct Contest {
    config: Config,
    docker_runner: DockerRunner,
}

impl Contest {
    pub fn new(config: Config) -> Result<Self> {
        let docker_runner = DockerRunner::new(config.clone(), "rust".to_string())?;
        Ok(Self {
            config,
            docker_runner,
        })
    }

    pub fn config(&self) -> &Config {
        &self.config
    }

    pub fn docker_runner(&mut self) -> &mut DockerRunner {
        &mut self.docker_runner
    }
} 