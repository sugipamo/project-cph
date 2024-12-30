#[cfg(test)]
mod helpers;

#[cfg(test)]
mod docker;

#[cfg(test)]
mod E2E;

#[cfg(test)]
mod tests {
    use super::helpers::{load_test_languages, setup_test_templates, cleanup_test_files};

    #[test]
    fn test_helpers() {
        let _lang_config = load_test_languages();
        setup_test_templates();
        cleanup_test_files();
    }
}

// テストモジュールの共通設定
#[cfg(test)]
pub fn setup() {
    // テスト用の環境変数を設定
    std::env::set_var("CPH_TEST", "1");
}

#[cfg(test)]
pub fn teardown() {
    // テスト用の環境変数をクリア
    std::env::remove_var("CPH_TEST");
} 