use std::path::PathBuf;
use cph::config::languages::LanguageConfig;

/// テスト用の言語設定を読み込む
pub fn load_test_languages() -> LanguageConfig {
    let config_path = PathBuf::from("src/config/languages.yaml");
    LanguageConfig::load(config_path)
        .expect("言語設定ファイルの読み込みに失敗しました")
}

/// テスト用のテンプレートディレクトリを作成
pub fn setup_test_templates() {
    let templates_dir = PathBuf::from("tests/fixtures/templates");
    if !templates_dir.exists() {
        std::fs::create_dir_all(&templates_dir).expect("テンプレートディレクトリの作成に失敗しました");
    }

    // Python用テンプレート
    let python_dir = templates_dir.join("python");
    if !python_dir.exists() {
        std::fs::create_dir_all(&python_dir).expect("Pythonテンプレートディレクトリの作成に失敗しました");
        std::fs::write(
            python_dir.join("main.py"),
            "def solve():\n    pass\n\nif __name__ == '__main__':\n    solve()\n"
        ).expect("Pythonテンプレートの作成に失敗しました");
    }

    // Rust用テンプレート
    let rust_dir = templates_dir.join("rust");
    if !rust_dir.exists() {
        std::fs::create_dir_all(&rust_dir).expect("Rustテンプレートディレクトリの作成に失敗しました");
        std::fs::write(
            rust_dir.join("main.rs"),
            "fn main() {\n    println!(\"Hello, world!\");\n}\n"
        ).expect("Rustテンプレートの作成に失敗しました");
    }
}

/// テスト用のディレクトリをクリーンアップ
pub fn cleanup_test_files() {
    let test_dir = PathBuf::from("tests/fixtures");
    if test_dir.exists() {
        std::fs::remove_dir_all(test_dir).expect("テストディレクトリの削除に失敗しました");
    }
} 