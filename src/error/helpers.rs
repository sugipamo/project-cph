use anyhow::anyhow;

pub fn fs_error(message: impl Into<String>) -> anyhow::Error {
    anyhow!(message.into())
}

pub fn docker_error(message: impl Into<String>) -> anyhow::Error {
    anyhow!(message.into())
}

pub fn config_error(message: impl Into<String>) -> anyhow::Error {
    anyhow!(message.into())
}

pub fn other_err(error: impl Into<String>, message: impl Into<String>) -> anyhow::Error {
    anyhow!("{}: {}", message.into(), error.into())
}