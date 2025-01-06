use std::path::Path;
use crate::error::CphError;
use crate::fs::error::io_err;

pub fn copy_to_container<P: AsRef<Path>>(container_id: &str, src: P, dest: P) -> Result<(), CphError> {
    let output = std::process::Command::new("docker")
        .arg("cp")
        .arg(src.as_ref())
        .arg(format!("{}:{}", container_id, dest.as_ref().display()))
        .output()
        .map_err(|e| io_err(e, "Dockerコンテナへのファイルコピー中のエラー".to_string()))?;

    if !output.status.success() {
        return Err(io_err(
            std::io::Error::new(
                std::io::ErrorKind::Other,
                String::from_utf8_lossy(&output.stderr).to_string()
            ),
            "Dockerコンテナへのファイルコピーに失敗".to_string()
        ));
    }

    Ok(())
}

pub fn copy_from_container<P: AsRef<Path>>(container_id: &str, src: P, dest: P) -> Result<(), CphError> {
    let output = std::process::Command::new("docker")
        .arg("cp")
        .arg(format!("{}:{}", container_id, src.as_ref().display()))
        .arg(dest.as_ref())
        .output()
        .map_err(|e| io_err(e, "Dockerコンテナからのファイルコピー中のエラー".to_string()))?;

    if !output.status.success() {
        return Err(io_err(
            std::io::Error::new(
                std::io::ErrorKind::Other,
                String::from_utf8_lossy(&output.stderr).to_string()
            ),
            "Dockerコンテナからのファイルコピーに失敗".to_string()
        ));
    }

    Ok(())
} 