use std::path::PathBuf;
use crate::error::Result;
use crate::contest::error::config_err;

pub struct TestCase {
    pub input: String,
    pub expected: String,
}

pub fn load_test_cases(test_dir: &PathBuf) -> Result<Vec<TestCase>> {
    let mut test_cases = Vec::new();

    let entries = std::fs::read_dir(test_dir)
        .map_err(|e| config_err(format!("テストディレクトリの読み取りに失敗しました: {}", e)))?;

    for entry in entries {
        let entry = entry
            .map_err(|e| config_err(format!("テストファイルの読み取りに失敗しました: {}", e)))?;
        let path = entry.path();

        if path.is_file() && path.extension().map_or(false, |ext| ext == "in") {
            let test_file = path.to_str().unwrap();
            let expected_path = PathBuf::from(test_file).with_extension("out");
            if !expected_path.exists() {
                return Err(config_err(format!("期待値ファイルが存在しません: {:?}", expected_path)));
            }

            let input = std::fs::read_to_string(&path)
                .map_err(|e| config_err(format!("入力ファイルの読み取りに失敗しました: {}", e)))?;

            let expected = std::fs::read_to_string(&expected_path)
                .map_err(|e| config_err(format!("期待値ファイルの読み取りに失敗しました: {}", e)))?;

            test_cases.push(TestCase { input, expected });
        }
    }

    Ok(test_cases)
}

#[cfg(test)]
mod tests {
    // テストの実装
} 