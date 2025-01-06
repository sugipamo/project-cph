use std::path::PathBuf;
use crate::error::{CphError, Result, helpers, ErrorExt};

#[derive(Debug)]
pub struct TestCase {
    pub input: String,
    pub expected: String,
}

pub fn load_test_cases(test_dir: &PathBuf) -> Result<Vec<TestCase>> {
    let entries = std::fs::read_dir(test_dir)
        .map_err(|e| helpers::config_not_found(
            format!("テストディレクトリの読み取りに失敗しました: {}", e)
        ))?;

    let mut test_cases = Vec::new();

    for entry in entries {
        let entry = entry
            .map_err(|e| helpers::config_not_found(
                format!("テストファイルの読み取りに失敗しました: {}", e)
            ))?;

        let path = entry.path();
        if !path.is_file() || !path.extension().map_or(false, |ext| ext == "in") {
            continue;
        }

        let expected_path = path.with_extension("out");
        if !expected_path.exists() {
            return Err(helpers::config_not_found(
                format!("期待値ファイルが存在しません: {:?}", expected_path)
            ).with_hint("テストケースには.inファイルと対応する.outファイルが必要です。"));
        }

        let input = std::fs::read_to_string(&path)
            .map_err(|e| helpers::config_not_found(
                format!("入力ファイルの読み取りに失敗しました: {}", e)
            ))?;

        let expected = std::fs::read_to_string(&expected_path)
            .map_err(|e| helpers::config_not_found(
                format!("期待値ファイルの読み取りに失敗しました: {}", e)
            ))?;

        test_cases.push(TestCase { input, expected });
    }

    Ok(test_cases)
}

pub fn config_not_found_err(path: String) -> CphError {
    helpers::config_not_found(path)
}

pub fn config_not_found_err_with_hint(path: String, hint: String) -> CphError {
    helpers::config_not_found(path).with_hint(hint)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_load_test_cases() -> Result<()> {
        let temp_dir = TempDir::new()
            .map_err(|e| helpers::config_not_found(
                format!("一時ディレクトリの作成に失敗しました: {}", e)
            ))?;
        let test_dir = temp_dir.path().to_path_buf();

        // テストケースファイルの作成
        fs::write(test_dir.join("test1.in"), "input1")
            .map_err(|e| helpers::config_not_found(
                format!("テストファイルの作成に失敗しました: {}", e)
            ))?;
        fs::write(test_dir.join("test1.out"), "output1")
            .map_err(|e| helpers::config_not_found(
                format!("テストファイルの作成に失敗しました: {}", e)
            ))?;

        let test_cases = load_test_cases(&test_dir)?;
        assert_eq!(test_cases.len(), 1);
        assert_eq!(test_cases[0].input, "input1");
        assert_eq!(test_cases[0].expected, "output1");

        Ok(())
    }
} 