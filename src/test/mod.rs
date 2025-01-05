use std::path::{Path, PathBuf};
use crate::config::Config;
use crate::contest::error::{Result, ContestError};

/// テストディレクトリのパスを取得
pub fn get_test_dir(config: &Config, problem_id: &str) -> Result<PathBuf> {
    let active_dir = config.get::<String>("languages.default.contest_dir.active")?;
    Ok(PathBuf::from(active_dir).join("test").join(problem_id))
}

/// テストケースを実行
pub async fn run_test_cases(test_dir: &Path) -> Result<()> {
    if !test_dir.exists() {
        return Err(ContestError::FileSystem {
            message: "テストディレクトリが存在しません".to_string(),
            source: std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "test directory not found"
            ),
            path: test_dir.to_path_buf(),
        });
    }

    // テストケースのファイルを列挙
    let mut test_files = Vec::new();
    for entry in std::fs::read_dir(test_dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
            test_files.push(path);
        }
    }

    if test_files.is_empty() {
        return Err(ContestError::Validation {
            message: "テストケースが見つかりません".to_string(),
        });
    }

    // 各テストケースを実行
    for test_file in test_files {
        let _input = std::fs::read_to_string(&test_file)?;
        let expected_path = test_file.with_extension("out");
        let _expected = std::fs::read_to_string(&expected_path)?;

        // TODO: 実際のテスト実行を実装
        println!("テストケース {}: 実行中...", test_file.display());
    }

    Ok(())
}

/// テストを実行
pub async fn run_test(
    config: &Config,
    problem_id: &str,
    _site_id: &str,
) -> Result<()> {
    let test_dir = get_test_dir(config, problem_id)?;
    run_test_cases(&test_dir).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    // テストの実装
} 