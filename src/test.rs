use std::path::Path;
use std::fs;
use tokio::fs as tokio_fs;
use crate::error::{Error, Result};
use crate::docker;
use crate::Config;
use colored::*;

pub struct TestResult {
    pub passed: bool,
    pub input: String,
    pub expected: String,
    pub actual: String,
    pub error: Option<String>,
}

pub async fn run_test(
    test_file: &Path,
    expected_output: &str,
    program_path: &Path,
    language: crate::Language,
) -> Result<TestResult> {
    let input = fs::read_to_string(test_file)
        .map_err(|e| Error::Io(e))?;

    let (actual_output, stderr) = docker::run_in_docker(
        program_path.parent().unwrap_or(Path::new(".")),
        &language,
        &[program_path.file_name().unwrap().to_str().unwrap()],
        Some(input.clone()),
    ).await?;

    let error = if !stderr.trim().is_empty() && !stderr.contains("Finished dev") {
        Some(stderr)
    } else {
        None
    };

    Ok(TestResult {
        passed: actual_output.trim() == expected_output.trim(),
        input,
        expected: expected_output.to_string(),
        actual: actual_output,
        error,
    })
}

fn classify_error(error: &str) -> (String, String) {
    if error.contains("error[E") {
        ("Compile Error:".red().bold().to_string(), format_compile_error(error))
    } else if error.contains("thread 'main' panicked") {
        ("Runtime Error:".red().bold().to_string(), format_runtime_error(error))
    } else if error.contains("killed") && error.contains("memory") {
        ("Memory Limit Exceeded:".yellow().bold().to_string(), error.to_string())
    } else if error.contains("timeout") {
        ("Time Limit Exceeded:".yellow().bold().to_string(), error.to_string())
    } else {
        ("Error:".red().bold().to_string(), error.to_string())
    }
}

fn format_compile_error(error: &str) -> String {
    let mut formatted = String::new();
    for line in error.lines() {
        if line.contains("error[") {
            // エラーコードを強調
            let parts: Vec<&str> = line.splitn(2, ": ").collect();
            if parts.len() == 2 {
                let code = parts[0].trim();
                formatted.push_str(&format!("{}: {}\n",
                    code.red().bold(),
                    parts[1]
                ));
                // エラーコードへのリンクを追加
                if let Some(error_code) = code.strip_prefix("error[") {
                    if let Some(code) = error_code.strip_suffix("]") {
                        formatted.push_str(&format!("  {} {}\n",
                            "Help:".green(),
                            format!("https://doc.rust-lang.org/error-index.html#{}", code).underline()
                        ));
                    }
                }
            }
        } else if line.contains("-->") {
            // ファイル位置を強調
            formatted.push_str(&format!("{}\n", line.blue()));
        } else if line.trim().starts_with("|") {
            // コードスニペットを強調
            formatted.push_str(&format!("{}\n", line.yellow()));
        } else if line.contains("help:") {
            // ヘルプメッセージを強調
            formatted.push_str(&format!("  {} {}\n",
                "Help:".green(),
                line.strip_prefix("help:").unwrap_or(line)
            ));
        } else {
            formatted.push_str(&format!("{}\n", line));
        }
    }
    formatted
}

fn format_runtime_error(error: &str) -> String {
    let mut formatted = String::new();
    for line in error.lines() {
        if line.contains("panicked at") {
            let parts: Vec<&str> = line.splitn(2, "panicked at").collect();
            formatted.push_str(&format!("thread panicked at {}\n",
                parts.get(1).unwrap_or(&line).red().bold()
            ));
        } else if line.contains("stack backtrace:") {
            formatted.push_str(&format!("{}\n", "Stack backtrace:".yellow().bold()));
        } else if line.starts_with("   ") {
            // スタックトレースのフレームを強調
            formatted.push_str(&format!("{}\n", line.blue()));
        } else {
            formatted.push_str(&format!("{}\n", line));
        }
    }
    formatted
}

fn print_diff(test_case: &str, result: &TestResult) {
    if result.passed {
        println!("Test case {} ... {}", test_case, "passed".green().bold());
    } else {
        println!("\nTest case {} ... {}", test_case, "failed".red().bold());
        
        // Input と Error を横に並べて表示
        let input_lines: Vec<&str> = result.input.trim().lines().collect();
        let (error_type, formatted_error) = if let Some(error) = &result.error {
            classify_error(error)
        } else {
            ("Wrong Answer:".red().bold().to_string(), String::new())
        };
        
        let error_lines: Vec<&str> = formatted_error.lines().collect();
        let max_lines = input_lines.len().max(error_lines.len());
        
        // Inputの最大長を計算
        let max_input_length = input_lines.iter()
            .map(|line| line.chars().count())
            .max()
            .unwrap_or(0)
            .max(10);
        
        let padding = max_input_length + 2;
        
        // ヘッダーを表示
        println!("{:<padding$} | {}", "Input:".yellow(), 
            if result.error.is_some() { error_type } else { "".normal().to_string() },
            padding=padding);
        println!("{}", "=".repeat(if result.error.is_some() { padding + 3 + 80 } else { padding }));
        
        // Input と Error を横に並べて表示
        for i in 0..max_lines {
            let input_line = input_lines.get(i).unwrap_or(&"");
            print!("{:<padding$}", input_line, padding=padding);
            
            if result.error.is_some() {
                print!(" | ");
                if let Some(error_line) = error_lines.get(i) {
                    print!("{}", error_line);
                }
            }
            println!();
        }

        // Wrong Answerの場合のみ期待値と実際の出力を表示
        if result.error.is_none() {
            let expected_lines: Vec<&str> = result.expected.trim().lines().collect();
            let actual_lines: Vec<&str> = result.actual.trim().lines().collect();
            
            let max_expected_length = expected_lines.iter()
                .map(|line| line.chars().count())
                .max()
                .unwrap_or(0)
                .max(10);

            let padding = max_expected_length + 2;
            println!("\n{:<padding$} | {}", "Expected:".yellow(), "Actual:".yellow(), padding=padding);
            println!("{}", "=".repeat(padding + 3 + 40));

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