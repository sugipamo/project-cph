use std::process::Command;
use crate::error::Result;
use crate::fs::io_err;

pub fn copy_to_container(container_id: &str, source: &str, target: &str) -> Result<()> {
    Command::new("docker")
        .args(["cp", source, &format!("{}:{}", container_id, target)])
        .output()
        .map_err(|e| {
            let msg = format!("ファイルのコピーに失敗しました: {}", e);
            io_err(e, msg)
        })?;

    Ok(())
}

pub fn copy_from_container(container_id: &str, source: &str, target: &str) -> Result<()> {
    let output = Command::new("docker")
        .args(["cp", &format!("{}:{}", container_id, source), target])
        .output()
        .map_err(|e| {
            let msg = format!("ファイルのコピーに失敗しました: {}", e);
            io_err(e, msg)
        })?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(io_err(
            std::io::Error::new(std::io::ErrorKind::Other, stderr.to_string()),
            "ファイルのコピーに失敗しました"
        ));
    }

    Ok(())
} 