use std::path::Path;
use std::fs;
use std::time::Instant;
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
    pub execution_time: std::time::Duration,
}

pub async fn run_test(
    test_file: &Path,
    expected_output: &str,
    program_path: &Path,
    language: crate::Language,
) -> Result<TestResult> {
    let input = fs::read_to_string(test_file)
        .map_err(|e| Error::Io(e))?;

    let output = docker::run_in_docker(
        program_path.parent().unwrap_or(Path::new(".")),
        &language,
        &[program_path.file_name().unwrap().to_str().unwrap()],
        Some(input.clone()),
    ).await?;

    let error = if !output.stderr.trim().is_empty() && !output.stderr.contains("Finished dev") {
        Some(output.stderr)
    } else {
        None
    };

    Ok(TestResult {
        passed: output.stdout.trim() == expected_output.trim(),
        input,
        expected: expected_output.to_string(),
        actual: output.stdout,
        error,
        execution_time: output.execution_time,
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
        println!("Test case {} ... {} ({:.3}s)", 
            test_case, 
            "passed".green().bold(),
            result.execution_time.as_secs_f64()
        );
    } else {
        println!("\nTest case {} ... {} ({:.3}s)", 
            test_case, 
            "failed".red().bold(),
            result.execution_time.as_secs_f64()
        );
        
        // まずInputを表示
        println!("Input:");
        println!("{}", "=".repeat(40));
        for line in result.input.trim().lines() {
            println!("{}", line);
        }

        // 標準出力を表示（エラーの有無に関わらず）
        let expected_lines: Vec<&str> = result.expected.trim().lines().collect();
        let actual_lines: Vec<&str> = result.actual.trim().lines().collect();
        
        if !actual_lines.is_empty() || !expected_lines.is_empty() {
            println!("\nOutput:");
            println!("{}", "=".repeat(40));
            
            let max_lines = expected_lines.len().max(actual_lines.len());
            println!("Expected:    | Actual:");
            println!("{}", "=".repeat(55));
            
            for i in 0..max_lines {
                let expected = expected_lines.get(i).unwrap_or(&"");
                let actual = actual_lines.get(i).unwrap_or(&"");
                
                if i < expected_lines.len() && i < actual_lines.len() && expected == actual {
                    println!("{:<12} | {}", expected, actual);
                } else {
                    if i < expected_lines.len() {
                        print!("{}", expected.green());
                    }
                    print!("{:<12}", "");
                    print!(" | ");
                    if i < actual_lines.len() {
                        print!("{}", actual.red());
                    }
                    println!();
                }
            }
        }

        // エラーがある場合はその後に表示
        if let Some(error) = &result.error {
            let (error_type, formatted_error) = classify_error(error);
            println!("\n{}", error_type);
            println!("{}", "=".repeat(40));
            println!("{}", formatted_error);
        }
        
        println!();
    }
}

pub async fn run_all_tests(
    test_dir: &Path,
    program_path: &Path,
    language: crate::Language,
) -> Result<(usize, usize, std::time::Duration)> {
    if !test_dir.exists() {
        return Ok((0, 0, std::time::Duration::from_secs(0)));
    }

    let mut total = 0;
    let mut test_futures = Vec::new();
    let mut max_execution_time = std::time::Duration::from_secs(0);

    let mut entries = tokio_fs::read_dir(test_dir).await
        .map_err(|e| Error::Io(e))?;

    // テストケースを収集
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

            let test_case = path.file_stem().unwrap().to_string_lossy().into_owned();
            let path = path.to_path_buf();
            let program_path = program_path.to_path_buf();
            
            // 各テストケースを非同期タスクとして準備
            test_futures.push(tokio::spawn(async move {
                let result = run_test(&path, &expected, &program_path, language).await?;
                Ok::<(String, TestResult), Error>((test_case, result))
            }));
        }
    }

    // 全テストを並列実行
    let mut passed = 0;
    for test_future in test_futures {
        match test_future.await {
            Ok(Ok((test_case, result))) => {
                if result.passed {
                    passed += 1;
                }
                max_execution_time = max_execution_time.max(result.execution_time);
                print_diff(&test_case, &result);
            },
            Ok(Err(e)) => println!("Test error: {}", e),
            Err(e) => println!("Task error: {}", e),
        }
    }

    Ok((passed, total, max_execution_time))
}

pub fn run(config: Config) -> Result<bool> {
    if let Ok(handle) = tokio::runtime::Handle::try_current() {
        handle.block_on(async {
            let (passed, total, max_time) = run_all_tests(
                &config.test_dir,
                &config.problem_file,
                config.language,
            ).await?;
            println!("\nTest results: {}/{} {} (max time: {:.3}s)", 
                passed.to_string().bold(), 
                total.to_string().bold(),
                if passed == total { "passed".green().bold() } else { "failed".red().bold() },
                max_time.as_secs_f64()
            );
            Ok(passed == total)
        })
    } else {
        tokio::runtime::Runtime::new()?.block_on(async {
            let (passed, total, max_time) = run_all_tests(
                &config.test_dir,
                &config.problem_file,
                config.language,
            ).await?;
            println!("\nTest results: {}/{} {} (max time: {:.3}s)", 
                passed.to_string().bold(), 
                total.to_string().bold(),
                if passed == total { "passed".green().bold() } else { "failed".red().bold() },
                max_time.as_secs_f64()
            );
            Ok(passed == total)
        })
    }
} 