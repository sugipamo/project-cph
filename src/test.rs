use std::path::Path;
use std::fs;
use tokio::fs as tokio_fs;
use crate::error::{Error, Result};
use crate::docker;
use crate::Config;

pub async fn run_test(
    test_file: &Path,
    expected_output: &str,
    program_path: &Path,
) -> Result<bool> {
    let input = fs::read_to_string(test_file)
        .map_err(|e| Error::Io(e))?;

    let (actual_output, _) = docker::execute_program(
        program_path.to_str().unwrap(),
        &[],
        Some(input),
    ).await?;

    Ok(actual_output.trim() == expected_output.trim())
}

pub async fn run_all_tests(
    test_dir: &Path,
    program_path: &Path,
) -> Result<(usize, usize)> {
    if !test_dir.exists() {
        return Ok((0, 0));
    }

    let mut total = 0;
    let mut passed = 0;

    let mut entries = tokio_fs::read_dir(test_dir).await
        .map_err(|e| Error::Io(e))?;

    while let Some(entry) = entries.next_entry().await
        .map_err(|e| Error::Io(e))? {
        let path = entry.path();
        if path.extension().map_or(false, |ext| ext == "in") {
            let out_path = path.with_extension("out");
            if !out_path.exists() {
                continue;
            }

            total += 1;
            let expected = fs::read_to_string(&out_path)
                .map_err(|e| Error::Io(e))?;

            if run_test(&path, &expected, program_path).await? {
                passed += 1;
            }
        }
    }

    Ok((passed, total))
}

pub fn run(config: Config) -> Result<()> {
    let runtime = tokio::runtime::Runtime::new()
        .map_err(|e| Error::Runtime(format!("Failed to create runtime: {}", e)))?;

    runtime.block_on(async {
        run_all_tests(&config.test_dir(), &config.problem_file()).await?;
        Ok(())
    })
} 