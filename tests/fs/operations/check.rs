use std::fs::{self, File};
use tempfile::TempDir;
use anyhow::Result;

use cph::fs::operations::check;

#[test]
fn test_exists() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_dir = temp_dir.path().join("test_dir");

    // ファイルが存在しない場合
    assert!(!check::exists(&test_file));

    // ファイルを作成
    File::create(&test_file)?;
    assert!(check::exists(&test_file));

    // ディレクトリを作成
    fs::create_dir(&test_dir)?;
    assert!(check::exists(&test_dir));

    Ok(())
}

#[test]
fn test_is_file() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_dir = temp_dir.path().join("test_dir");

    // ファイルを作成
    File::create(&test_file)?;
    fs::create_dir(&test_dir)?;

    assert!(check::is_file(&test_file));
    assert!(!check::is_file(&test_dir));
    assert!(!check::is_file(temp_dir.path().join("non_existent.txt")));

    Ok(())
}

#[test]
fn test_is_directory() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");
    let test_dir = temp_dir.path().join("test_dir");

    // ファイルとディレクトリを作成
    File::create(&test_file)?;
    fs::create_dir(&test_dir)?;

    assert!(check::is_directory(&test_dir));
    assert!(!check::is_directory(&test_file));
    assert!(!check::is_directory(temp_dir.path().join("non_existent_dir")));

    Ok(())
}

#[test]
fn test_verify_basic_permissions() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");

    // ファイルが存在しない場合
    assert!(check::verify_basic_permissions(&test_file, false).is_err());

    // ファイルを作成
    File::create(&test_file)?;

    // 読み取り権限のみの確認
    assert!(check::verify_basic_permissions(&test_file, false).is_ok());

    // 書き込み権限の確認（読み取り専用でない場合はエラー）
    {
        let metadata = fs::metadata(&test_file)?;
        let mut perms = metadata.permissions();
        perms.set_readonly(true);
        fs::set_permissions(&test_file, perms)?;
        assert!(check::verify_basic_permissions(&test_file, true).is_ok());
    }

    {
        let metadata = fs::metadata(&test_file)?;
        let mut perms = metadata.permissions();
        perms.set_readonly(false);
        fs::set_permissions(&test_file, perms)?;
        assert!(check::verify_basic_permissions(&test_file, true).is_err());
    }

    Ok(())
}

#[test]
fn test_verify_permissions() -> Result<()> {
    let temp_dir = TempDir::new()?;
    let test_file = temp_dir.path().join("test.txt");

    // ファイルが存在しない場合
    assert!(check::verify_permissions(&test_file, false).is_err());

    // ファイルを作成
    File::create(&test_file)?;

    // 読み取り権限のみの確認
    assert!(check::verify_permissions(&test_file, false).is_ok());

    // 書き込み権限の確認
    assert!(check::verify_permissions(&test_file, true).is_ok());

    Ok(())
}

#[cfg(unix)]
mod unix_tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn test_unix_permissions() -> Result<()> {
        let temp_dir = TempDir::new()?;
        let test_file = temp_dir.path().join("test.txt");

        // ファイルを作成
        File::create(&test_file)?;

        // 読み取り権限を削除
        let metadata = fs::metadata(&test_file)?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o222); // 書き込みのみ
        fs::set_permissions(&test_file, perms)?;

        assert!(check::verify_permissions(&test_file, false).is_err());

        // 書き込み権限を削除
        let metadata = fs::metadata(&test_file)?;
        let mut perms = metadata.permissions();
        perms.set_mode(0o444); // 読み取りのみ
        fs::set_permissions(&test_file, perms)?;

        assert!(check::verify_permissions(&test_file, true).is_err());

        Ok(())
    }
} 