use crate::error::{helpers, CphError, ErrorExt};

#[derive(Debug, Clone)]
pub struct TestCase {
    pub input: String,
    pub expected: String,
    pub path: String,
}

pub fn read_test_cases(test_dir: &str) -> Result<Vec<TestCase>, CphError> {
    let entries = std::fs::read_dir(test_dir)
        .map_err(|e| helpers::config_not_found(
            "テストディレクトリの読み取り",
            format!("ディレクトリ: {}, エラー: {}", test_dir, e)
        ))?;

    let mut test_cases = Vec::new();
    for entry in entries {
        let entry = entry
            .map_err(|e| helpers::config_not_found(
                "テストファイルの読み取り",
                format!("エラー: {}", e)
            ))?;

        let path = entry.path();
        if path.extension().map_or(false, |ext| ext == "in") {
            let expected_path = path.with_extension("out");
            if !expected_path.exists() {
                return Err(helpers::config_not_found(
                    "期待値ファイルの確認",
                    format!("ファイル: {:?}", expected_path)
                ).with_hint("テストケースには.inファイルと対応する.outファイルが必要です。"));
            }

            let input = std::fs::read_to_string(&path)
                .map_err(|e| helpers::config_not_found(
                    "入力ファイルの読み取り",
                    format!("ファイル: {:?}, エラー: {}", path, e)
                ))?;

            let expected = std::fs::read_to_string(&expected_path)
                .map_err(|e| helpers::config_not_found(
                    "期待値ファイルの読み取り",
                    format!("ファイル: {:?}, エラー: {}", expected_path, e)
                ))?;

            test_cases.push(TestCase {
                input,
                expected,
                path: path.to_string_lossy().into_owned(),
            });
        }
    }

    Ok(test_cases)
}

pub fn not_found_err(path: String) -> CphError {
    helpers::config_not_found("ファイル検索", path)
}

pub fn not_found_err_with_hint(path: String, hint: String) -> CphError {
    helpers::config_not_found("ファイル検索", path).with_hint(hint)
} 