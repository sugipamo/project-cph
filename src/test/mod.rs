use std::path::{Path, PathBuf};
use crate::config::Config;
use crate::contest::error::{ContestError, ContestResult};

/// テストディレクトリのパスを取得
pub fn get_test_dir(config: &Config, problem_id: &str) -> ContestResult<PathBuf> {
    let default_lang = config.get::<String>("languages.default")
        .map_err(|e| ContestError::Config(e.to_string()))?;
    let active_dir = config.get::<String>(&format!("languages.{}.contest_dir.active", default_lang))
        .map_err(|e| ContestError::Config(e.to_string()))?;
    Ok(PathBuf::from(active_dir).join("test").join(problem_id))
}

/// テストケースを実行
pub async fn run_test_cases(test_dir: &Path) -> ContestResult<()> {
    if !test_dir.exists() {
        return Err(ContestError::Contest(
            format!("テストディレクトリが存在しません: {}", test_dir.display())
        ));
    }

    // テストケースのファイルを列挙
    let mut test_files = Vec::new();
    for entry in std::fs::read_dir(test_dir)
        .map_err(|e| ContestError::Io(e))? {
        let entry = entry.map_err(|e| ContestError::Io(e))?;
        let path = entry.path();
        if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
            test_files.push(path);
        }
    }

    if test_files.is_empty() {
        return Err(ContestError::Contest(
            "テストケースが見つかりません".to_string()
        ));
    }

    // 各テストケースを実行
    for test_file in test_files {
        let input = std::fs::read_to_string(&test_file)
            .map_err(|e| ContestError::Io(e))?;
        let expected_path = test_file.with_extension("out");
        let expected = std::fs::read_to_string(&expected_path)
            .map_err(|e| ContestError::Io(e))?;

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
) -> ContestResult<()> {
    let test_dir = get_test_dir(config, problem_id)?;
    run_test_cases(&test_dir).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    // テストの実装
} 