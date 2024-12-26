use std::path::PathBuf;
use std::process::{Command as ProcessCommand, Stdio};
use std::time::Duration;
use thiserror::Error;
use tokio::process::Command as TokioCommand;
use tokio::time::timeout;

#[derive(Debug, Error)]
pub enum Error {
    #[error("Invalid {kind}: {value}")]
    Invalid { kind: &'static str, value: String },
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Test execution error: {0}")]
    TestExecution(String),
    #[error("Test timeout")]
    TestTimeout,
}

#[derive(Debug, Clone, Copy)]
pub enum ContestType {
    Abc,
    Arc,
    Ahc,
    Other,
}

impl ContestType {
    pub fn as_str(&self) -> &'static str {
        match self {
            ContestType::Abc => "abc",
            ContestType::Arc => "arc",
            ContestType::Ahc => "ahc",
            ContestType::Other => "other",
        }
    }

    pub fn from_id(contest_id: &str) -> Self {
        match contest_id.get(..3) {
            Some("abc") => ContestType::Abc,
            Some("arc") => ContestType::Arc,
            Some("ahc") => ContestType::Ahc,
            _ => ContestType::Other,
        }
    }
}

#[derive(Debug, Clone)]
pub enum Language {
    Rust,
    PyPy,
}

impl Language {
    pub fn extension(&self) -> &str {
        match self {
            Language::Rust => "rs",
            Language::PyPy => "py",
        }
    }

    pub fn template_name(&self) -> &str {
        match self {
            Language::Rust => "main.rs",
            Language::PyPy => "main.py",
        }
    }

    pub fn default_content(&self) -> &str {
        match self {
            Language::Rust => "fn main() {\n    \n}\n",
            Language::PyPy => "def main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
        }
    }
}

impl TryFrom<&str> for Language {
    type Error = Error;

    fn try_from(s: &str) -> Result<Self, Self::Error> {
        match s.to_lowercase().as_str() {
            "rust" | "r" => Ok(Language::Rust),
            "pypy" | "py" => Ok(Language::PyPy),
            _ => Err(Error::Invalid {
                kind: "language",
                value: s.to_string(),
            }),
        }
    }
}

#[derive(Debug, Clone)]
pub enum Command {
    Open,
    Test,
    Submit,
}

impl TryFrom<&str> for Command {
    type Error = Error;

    fn try_from(s: &str) -> Result<Self, Self::Error> {
        match s.to_lowercase().as_str() {
            "open" | "o" => Ok(Command::Open),
            "test" | "t" => Ok(Command::Test),
            "submit" | "s" => Ok(Command::Submit),
            _ => Err(Error::Invalid {
                kind: "command",
                value: s.to_string(),
            }),
        }
    }
}

#[derive(Debug, Clone)]
pub struct Config {
    pub contest_id: String,
    pub language: Language,
    pub command: Command,
    pub problem_id: String,
    pub workspace_dir: PathBuf,
}

impl Config {
    pub fn new(
        contest_id: String,
        language: Language,
        command: Command,
        problem_id: String,
    ) -> Self {
        let workspace_dir = PathBuf::from("workspace");
        Self {
            contest_id,
            language,
            command,
            problem_id,
            workspace_dir,
        }
    }

    pub fn contest_type(&self) -> ContestType {
        ContestType::from_id(&self.contest_id)
    }

    pub fn contest_dir(&self) -> PathBuf {
        self.workspace_dir
            .join(self.contest_type().as_str())
            .join(&self.contest_id)
    }

    pub fn problem_file(&self) -> PathBuf {
        self.contest_dir()
            .join(format!("{}.{}", self.problem_id, self.language.extension()))
    }

    pub fn template_path(&self) -> PathBuf {
        self.contest_dir()
            .join("template")
            .join(self.language.template_name())
    }

    pub fn test_dir(&self) -> PathBuf {
        self.contest_dir().join("test")
    }

    pub fn generator_file(&self) -> PathBuf {
        let ext = self.language.extension();
        self.contest_dir().join(format!("{}_gen.{}", self.problem_id, ext))
    }
}

pub fn run(config: Config) -> Result<(), Error> {
    match config.command {
        Command::Open => open(config),
        Command::Test => test(config),
        Command::Submit => submit(config),
    }
}

fn open(config: Config) -> Result<(), Error> {
    // Create contest directory if it doesn't exist
    std::fs::create_dir_all(config.contest_dir())?;
    
    // Create problem file
    if config.template_path().exists() {
        std::fs::copy(config.template_path(), config.problem_file())?;
        println!("Created problem file from template: {:?}", config.problem_file());
    } else {
        std::fs::write(config.problem_file(), config.language.default_content())?;
        println!("Created empty problem file: {:?}", config.problem_file());
    }
    Ok(())
}

#[derive(Debug)]
struct TestCase {
    input: String,
    expected: String,
    name: String,
}

impl TestCase {
    fn from_files(input_path: &PathBuf, output_path: &PathBuf) -> Result<Self, Error> {
        let input = std::fs::read_to_string(input_path)
            .map_err(|e| Error::TestExecution(format!("Failed to read input file: {}", e)))?;
        let expected = std::fs::read_to_string(output_path)
            .map_err(|e| Error::TestExecution(format!("Failed to read output file: {}", e)))?;
        let name = input_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown")
            .to_string();

        Ok(TestCase {
            input,
            expected,
            name,
        })
    }
}

#[derive(Debug)]
struct TestResult {
    name: String,
    status: TestStatus,
    execution_time: Duration,
}

#[derive(Debug)]
enum TestStatus {
    Pass,
    Fail { got: String, expected: String },
    Error(String),
    Timeout,
}

async fn execute_test(config: &Config, test_case: TestCase) -> TestResult {
    let start = std::time::Instant::now();
    
    let program = match config.language {
        Language::Rust => {
            let status = ProcessCommand::new("rustc")
                .arg(config.problem_file())
                .arg("-o")
                .arg("problem")
                .status();

            match status {
                Ok(exit) if exit.success() => "./problem",
                _ => {
                    return TestResult {
                        name: test_case.name,
                        status: TestStatus::Error("Compilation failed".to_string()),
                        execution_time: start.elapsed(),
                    };
                }
            }
        }
        Language::PyPy => "pypy3",
    };

    let problem_path = config.problem_file();
    let mut command = TokioCommand::new(program);
    if matches!(config.language, Language::PyPy) {
        command.arg(problem_path);
    }

    let mut child = match command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(e) => {
            return TestResult {
                name: test_case.name,
                status: TestStatus::Error(format!("Failed to spawn process: {}", e)),
                execution_time: start.elapsed(),
            };
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        use tokio::io::AsyncWriteExt;
        if let Err(e) = stdin.write_all(test_case.input.as_bytes()).await {
            return TestResult {
                name: test_case.name,
                status: TestStatus::Error(format!("Failed to write to stdin: {}", e)),
                execution_time: start.elapsed(),
            };
        }
    }

    match timeout(Duration::from_secs(5), child.wait_with_output()).await {
        Ok(Ok(output)) => {
            let got = String::from_utf8_lossy(&output.stdout).into_owned();
            let status = if got.trim() == test_case.expected.trim() {
                TestStatus::Pass
            } else {
                TestStatus::Fail {
                    got,
                    expected: test_case.expected,
                }
            };

            TestResult {
                name: test_case.name,
                status,
                execution_time: start.elapsed(),
            }
        }
        Ok(Err(e)) => TestResult {
            name: test_case.name,
            status: TestStatus::Error(format!("Execution failed: {}", e)),
            execution_time: start.elapsed(),
        },
        Err(_) => TestResult {
            name: test_case.name,
            status: TestStatus::Timeout,
            execution_time: Duration::from_secs(5),
        }
    }
}

fn test(config: Config) -> Result<(), Error> {
    let test_dir = config.test_dir();
    if !test_dir.exists() {
        return Err(Error::TestExecution(format!(
            "Test directory not found: {:?}",
            test_dir
        )));
    }

    let runtime = tokio::runtime::Runtime::new()
        .map_err(|e| Error::TestExecution(format!("Failed to create runtime: {}", e)))?;

    runtime.block_on(async {
        let mut test_cases = Vec::new();
        
        // Collect sample test cases
        for entry in std::fs::read_dir(&test_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("in") {
                let input_path = path.clone();
                let output_path = path.with_extension("out");
                if output_path.exists() {
                    if let Ok(test_case) = TestCase::from_files(&input_path, &output_path) {
                        test_cases.push(test_case);
                    }
                }
            }
        }

        // Execute tests in parallel
        let mut handles = Vec::new();
        for test_case in test_cases {
            let config = config.clone();  // Clone config for each task
            handles.push(tokio::spawn(async move {
                execute_test(&config, test_case).await
            }));
        }

        // Collect results
        let mut all_passed = true;
        for handle in handles {
            let result = handle.await.map_err(|e| Error::TestExecution(e.to_string()))?;
            match result.status {
                TestStatus::Pass => {
                    println!(
                        "Test {} passed ({:?})",
                        result.name,
                        result.execution_time
                    );
                }
                TestStatus::Fail { got, expected } => {
                    all_passed = false;
                    println!("Test {} failed", result.name);
                    println!("Expected:\n{}", expected);
                    println!("Got:\n{}", got);
                }
                TestStatus::Error(e) => {
                    all_passed = false;
                    println!("Test {} error: {}", result.name, e);
                }
                TestStatus::Timeout => {
                    all_passed = false;
                    println!("Test {} timed out (> 5s)", result.name);
                }
            }
        }

        if !all_passed {
            return Err(Error::TestExecution("Some tests failed".to_string()));
        }

        Ok(())
    })
}

fn submit(_config: Config) -> Result<(), Error> {
    println!("Submit command not implemented yet");
    Ok(())
}
