use std::path::{Path, PathBuf};
use crate::error::{helpers, Result};
use crate::error::config::ConfigErrorKind;

pub fn validate_expected_file(expected_path: impl AsRef<Path>) -> Result<()> {
    if !expected_path.as_ref().exists() {
        return Err(helpers::config_error(
            ConfigErrorKind::NotFound,
            format!("期待値ファイルが見つかりません: {:?}", expected_path.as_ref())
        ));
    }
    Ok(())
}

pub fn find_test_files(test_dir: impl AsRef<Path>) -> Result<Vec<PathBuf>> {
    let test_dir = test_dir.as_ref();
    if !test_dir.exists() {
        return Err(helpers::config_error(
            ConfigErrorKind::NotFound,
            format!("テストディレクトリが見つかりません: {}", test_dir.display())
        ));
    }

    let entries = std::fs::read_dir(test_dir)
        .map_err(|e| helpers::config_error(
            ConfigErrorKind::IO,
            format!("テストディレクトリの読み取りに失敗しました: {}", e)
        ))?;

    let mut test_files = Vec::new();
    for entry in entries {
        let entry = entry
            .map_err(|e| helpers::config_error(
                ConfigErrorKind::IO,
                format!("テストファイルの読み取りに失敗しました: {}", e)
            ))?;

        let path = entry.path();
        if path.is_file() {
            let expected_path = path.with_extension("out");
            if !expected_path.exists() {
                return Err(helpers::config_error(
                    ConfigErrorKind::NotFound,
                    format!("期待値ファイルが見つかりません: {:?}", expected_path)
                ));
            }

            let _input = std::fs::read_to_string(&path)
                .map_err(|e| helpers::config_error(
                    ConfigErrorKind::IO,
                    format!("入力ファイルの読み取りに失敗しました: {:?}, {}", path, e)
                ))?;

            let _expected = std::fs::read_to_string(&expected_path)
                .map_err(|e| helpers::config_error(
                    ConfigErrorKind::IO,
                    format!("期待値ファイルの読み取りに失敗しました: {:?}, {}", expected_path, e)
                ))?;

            test_files.push(path);
        }
    }

    Ok(test_files)
}

pub fn not_found_err(path: impl Into<String>) -> crate::error::Error {
    helpers::config_error(
        ConfigErrorKind::NotFound,
        format!("ファイルが見つかりません: {}", path.into())
    )
}

pub fn not_found_err_with_hint(path: impl Into<String>, hint: &'static str) -> crate::error::Error {
    helpers::config_error(
        ConfigErrorKind::NotFound,
        format!("ファイルが見つかりません: {}", path.into())
    ).with_hint(hint)
}