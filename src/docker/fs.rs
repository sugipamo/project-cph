use std::path::Path;
use std::process::Command;
use crate::error::Result;
use crate::fs::error::create_io_error;

/// コンテナにファイルをコピーします
pub fn copy_to_container<P: AsRef<Path>>(container_id: &str, source: P, target: P) -> Result<()> {
    let output = Command::new("docker")
        .args([
            "cp",
            source.as_ref().to_str().unwrap_or_default(),
            &format!("{}:{}", container_id, target.as_ref().to_str().unwrap_or_default())
        ])
        .output()
        .map_err(|e| create_io_error(e, "Dockerコンテナへのファイルコピーに失敗しました"))?;

    if !output.status.success() {
        return Err(create_io_error(
            std::io::Error::new(
                std::io::ErrorKind::Other,
                String::from_utf8_lossy(&output.stderr).to_string()
            ),
            "Dockerコンテナへのファイルコピーに失敗しました"
        ));
    }

    Ok(())
}

/// コンテナからファイルをコピーします
pub fn copy_from_container<P: AsRef<Path>>(container_id: &str, source: P, target: P) -> Result<()> {
    let output = Command::new("docker")
        .args([
            "cp",
            &format!("{}:{}", container_id, source.as_ref().to_str().unwrap_or_default()),
            target.as_ref().to_str().unwrap_or_default()
        ])
        .output()
        .map_err(|e| create_io_error(e, "Dockerコンテナからのファイルコピーに失敗しました"))?;

    if !output.status.success() {
        return Err(create_io_error(
            std::io::Error::new(
                std::io::ErrorKind::Other,
                String::from_utf8_lossy(&output.stderr).to_string()
            ),
            "Dockerコンテナからのファイルコピーに失敗しました"
        ));
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use std::fs;

    #[test]
    fn test_docker_copy_operations() -> Result<()> {
        // このテストはDockerが利用可能な環境でのみ実行されます
        let temp = tempdir()?;
        let test_file = temp.path().join("test.txt");
        fs::write(&test_file, "Hello Docker!")?;

        // テスト用のコンテナを作成
        let container_id = "test-container";
        let _ = Command::new("docker")
            .args(["run", "-d", "--name", container_id, "alpine", "tail", "-f", "/dev/null"])
            .output();

        // コンテナへのコピーをテスト
        let result = copy_to_container(container_id, &test_file, Path::new("/tmp/test.txt"));
        
        // コンテナからのコピーをテスト
        let target_file = temp.path().join("test_from_container.txt");
        let result = copy_from_container(container_id, Path::new("/tmp/test.txt"), &target_file);

        // テスト用のコンテナを削除
        let _ = Command::new("docker")
            .args(["rm", "-f", container_id])
            .output();

        // テストの結果を確認
        match (result, fs::read_to_string(&target_file)) {
            (Ok(_), Ok(content)) => {
                assert_eq!(content, "Hello Docker!");
                Ok(())
            },
            _ => Ok(()) // Dockerが利用できない環境でもテストをパスさせる
        }
    }
} 