use crate::contest::core::test::TestManager;
use crate::config::Config;
use crate::contest::error::Result;

/// テストを実行
pub async fn run_test(
    config: &Config,
    problem_id: &str,
    site_id: &str,
) -> Result<()> {
    let test_dir = config.get::<String>("languages.default.contest_dir.active")?;
    let test_dir = std::path::PathBuf::from(test_dir).join("test").join(problem_id);
    
    let generator_path = test_dir.join("generator");
    let tester_path = test_dir.join("tester");
    let language = config.get::<String>("languages.default.name")?;

    let test_manager = TestManager::new(
        test_dir,
        generator_path,
        tester_path,
        language,
    )?;

    test_manager.run(problem_id)
}

#[cfg(test)]
mod tests {
    // テストの実装
} 