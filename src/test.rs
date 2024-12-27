use std::path::Path;
use std::fs;
use tokio::fs as tokio_fs;
use crate::error::{Error, Result};
use crate::docker;
use crate::Config;
use colored::*;

struct TestResult {
    passed: bool,
    input: String,
    expected: String,
    actual: String,
}

pub async fn run_test(
    test_file: &Path,
    expected_output: &str,
    program_path: &Path,
    language: crate::Language,
) -> Result<TestResult> {
    let input = fs::read_to_string(test_file)
        .map_err(|e| Error::Io(e))?;

    let (actual_output, _) = docker::run_in_docker(
        program_path.parent().unwrap_or(Path::new(".")),
        &language,
        &[program_path.file_name().unwrap().to_str().unwrap()],
    ).await?;

    Ok(TestResult {
        passed: actual_output.trim() == expected_output.trim(),
        input,
        expected: expected_output.to_string(),
        actual: actual_output,
    })
}

fn print_diff(test_case: &str, result: &TestResult) {
    if result.passed {
        println!("Test case {} ... {}", test_case, "passed".green().bold());
    } else {
        println!("\nTest case {} ... {}", test_case, "failed".red().bold());
        println!("{}", "Input:".yellow());
        println!("```");
        println!("{}", result.input.trim());
        println!("```");

        // 期待値と実際の出力を並べて表示
        let expected_lines: Vec<&str> = result.expected.trim().lines().collect();
        let actual_lines: Vec<&str> = result.actual.trim().lines().collect();
        
        // 期待値の最大長を計算
        let max_expected_length = expected_lines.iter()
            .map(|line| line.chars().count())
            .max()
            .unwrap_or(0)
            .max(10); // 最小幅を10文字に設定

        let padding = max_expected_length + 2; // 2文字分の余白を追加
        println!("\n{:<padding$} | {}", "Expected:".yellow(), "Actual:".yellow(), padding=padding);
        println!("{}", "=".repeat(padding + 3 + 40)); // 区切り線の長さを調整

        let max_lines = expected_lines.len().max(actual_lines.len());

        for i in 0..max_lines {
            let expected = expected_lines.get(i).unwrap_or(&"");
            let actual = actual_lines.get(i).unwrap_or(&"");
            
            if i < expected_lines.len() && i < actual_lines.len() && expected == actual {
                println!("{:<padding$} | {}", expected, actual, padding=padding);
            } else {
                if i < expected_lines.len() {
                    print!("{}", expected.green());
                }
                print!("{:<padding$}", "", padding=padding - expected.chars().count());
                print!(" | ");
                if i < actual_lines.len() {
                    print!("{}", actual.red());
                }
                println!();
            }
        }
        println!();
    }
}

pub async fn run_all_tests(
    test_dir: &Path,
    program_path: &Path,
    language: crate::Language,
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

            let test_case = path.file_stem().unwrap().to_string_lossy();
            let result = run_test(&path, &expected, program_path, language).await?;
            
            if result.passed {
                passed += 1;
            }
            print_diff(&test_case, &result);
        }
    }

    Ok((passed, total))
}

pub fn run(config: Config) -> Result<()> {
    if let Ok(handle) = tokio::runtime::Handle::try_current() {
        handle.block_on(async {
            let (passed, total) = run_all_tests(
                &config.test_dir,
                &config.problem_file,
                config.language,
            ).await?;
            println!("\nTest results: {}/{} {}", 
                passed.to_string().bold(), 
                total.to_string().bold(),
                if passed == total { "passed".green().bold() } else { "failed".red().bold() }
            );
            Ok(())
        })
    } else {
        tokio::runtime::Runtime::new()?.block_on(async {
            let (passed, total) = run_all_tests(
                &config.test_dir,
                &config.problem_file,
                config.language,
            ).await?;
            println!("\nTest results: {}/{} {}", 
                passed.to_string().bold(), 
                total.to_string().bold(),
                if passed == total { "passed".green().bold() } else { "failed".red().bold() }
            );
            Ok(())
        })
    }
} 