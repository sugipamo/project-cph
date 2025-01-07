use crate::error::docker::DockerErrorKind;
use crate::error::Result;
use crate::docker_error;

pub fn validate_image_name(image_name: &str) -> Result<()> {
    if image_name.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "イメージ名が指定されていません"
        ));
    }
    Ok(())
}

pub fn validate_container_name(container_name: &str) -> Result<()> {
    if container_name.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "コンテナ名が指定されていません"
        ));
    }
    Ok(())
}

pub fn validate_command(command: &str) -> Result<()> {
    if command.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "コマンドが指定されていません"
        ));
    }
    Ok(())
}

pub fn validate_working_dir(working_dir: &str) -> Result<()> {
    if working_dir.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "作業ディレクトリが指定されていません"
        ));
    }
    Ok(())
}

pub fn validate_volume(source: &str, target: &str) -> Result<()> {
    if source.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "ボリュームのソースパスが指定されていません"
        ));
    }
    if target.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "ボリュームのターゲットパスが指定されていません"
        ));
    }
    Ok(())
}

pub fn validate_env(key: &str, value: &str) -> Result<()> {
    if key.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "環境変数のキーが指定されていません"
        ));
    }
    if value.is_empty() {
        return Err(docker_error!(
            DockerErrorKind::ValidationError,
            "環境変数の値が指定されていません"
        ));
    }
    Ok(())
} 