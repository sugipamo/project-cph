use std::process::Command;
use crate::error::Result;
use crate::docker::error::execution_err;

pub struct DockerCommand {
    command: Command,
}

impl DockerCommand {
    pub fn new(name: &str) -> Self {
        let mut command = Command::new("docker");
        command.arg(name);
        Self { command }
    }

    pub fn arg<S: AsRef<str>>(mut self, arg: S) -> Self {
        self.command.arg(arg.as_ref());
        self
    }

    pub fn args<I, S>(mut self, args: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        for arg in args {
            self.command.arg(arg.as_ref());
        }
        self
    }

    pub fn execute(&mut self) -> Result<String> {
        let output = self.command
            .output()
            .map_err(|e| execution_err("コマンド実行", e.to_string()))?;

        if !output.status.success() {
            let error = String::from_utf8_lossy(&output.stderr);
            return Err(execution_err(
                "コマンド実行",
                format!("コマンドの実行に失敗: {}", error)
            ));
        }

        String::from_utf8(output.stdout)
            .map_err(|e| execution_err("コマンド実行", e.to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_docker_command() {
        let mut cmd = DockerCommand::new("version")
            .arg("--format")
            .arg("{{.Server.Version}}");

        let result = cmd.execute();
        assert!(result.is_ok());
    }

    #[test]
    fn test_invalid_command() {
        let mut cmd = DockerCommand::new("invalid_command");
        let result = cmd.execute();
        assert!(result.is_err());
    }
} 