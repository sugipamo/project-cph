use std::path::PathBuf;
use std::time::Duration;
use thiserror::Error;

pub mod docker;

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

impl Error {
    pub fn test_execution(msg: impl Into<String>) -> Self {
        Error::TestExecution(msg.into())
    }
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

    pub fn generator_template(&self) -> &str {
        match self {
            Language::Rust => r#"fn generate_case() -> (String, String) {
    // TODO: カスタムケースの生成ロジックを実装
    let input = String::new();
    let output = String::new();
    (input, output)
}

fn main() {
    // 生成するテストケースの数を指定
    let n_cases = 1;
    
    let mut inputs = Vec::new();
    let mut outputs = Vec::new();
    
    for _ in 0..n_cases {
        let (input, output) = generate_case();
        inputs.push(input);
        outputs.push(output);
    }
    
    // 入力ケースの出力
    for input in inputs {
        println!("{}", input);
    }
    
    // 期待される出力の出力（標準エラー出力）
    for output in outputs {
        eprintln!("{}", output);
    }
}"#,
            Language::PyPy => r#"def generate_case():
    # TODO: カスタムケースの生成ロジックを実装
    input_data = ""
    output_data = ""
    return input_data, output_data

def main():
    # 生成するテストケースの数を指定
    n_cases = 1
    
    inputs = []
    outputs = []
    
    for _ in range(n_cases):
        input_data, output_data = generate_case()
        inputs.append(input_data)
        outputs.append(output_data)
    
    # 入力ケースの出力
    for input_data in inputs:
        print(input_data)
    
    # 期待される出力の出力（標準エラー出力）
    import sys
    for output_data in outputs:
        print(output_data, file=sys.stderr)

if __name__ == "__main__":
    main()"#,
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
    Generate,
}

impl TryFrom<&str> for Command {
    type Error = Error;

    fn try_from(s: &str) -> Result<Self, Self::Error> {
        match s.to_lowercase().as_str() {
            "open" | "o" => Ok(Command::Open),
            "test" | "t" => Ok(Command::Test),
            "submit" | "s" => Ok(Command::Submit),
            "generate" | "g" => Ok(Command::Generate),
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

    fn join_contest_dir(&self, path: impl AsRef<std::path::Path>) -> PathBuf {
        self.contest_dir().join(path)
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
        self.join_contest_dir(format!("{}.{}", self.problem_id, self.language.extension()))
    }

    pub fn template_path(&self) -> PathBuf {
        self.join_contest_dir("template").join(self.language.template_name())
    }

    pub fn test_dir(&self) -> PathBuf {
        self.join_contest_dir("test")
    }

    pub fn generator_file(&self) -> PathBuf {
        self.join_contest_dir(format!("{}_gen.{}", self.problem_id, self.language.extension()))
    }
}

pub fn run(config: Config) -> Result<(), Error> {
    match config.command {
        Command::Open => open(config),
        Command::Test => test(config),
        Command::Submit => submit(config),
        Command::Generate => generate(config),
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
    fn read_file(path: &PathBuf, file_type: &str) -> Result<String, Error> {
        std::fs::read_to_string(path)
            .map_err(|e| Error::test_execution(format!("Failed to read {} file: {}", file_type, e)))
    }

    fn from_files(input_path: &PathBuf, output_path: &PathBuf) -> Result<Self, Error> {
        let input = Self::read_file(input_path, "input")?;
        let expected = Self::read_file(output_path, "output")?;
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

impl TestResult {
    fn new(name: String, status: TestStatus, execution_time: Duration) -> Self {
        Self {
            name,
            status,
            execution_time,
        }
    }

    fn error(name: String, error: impl Into<String>, start: std::time::Instant) -> Self {
        Self::new(
            name,
            TestStatus::Error(error.into()),
            start.elapsed(),
        )
    }

    fn display(&self) -> bool {
        match &self.status {
            TestStatus::Pass => {
                println!(
                    "Test {} passed ({:?})",
                    self.name,
                    self.execution_time
                );
                true
            }
            TestStatus::Fail { got, expected } => {
                println!("Test {} failed", self.name);
                println!("Expected:\n{}", expected);
                println!("Got:\n{}", got);
                false
            }
            TestStatus::Error(e) => {
                println!("Test {} error: {}", self.name, e);
                false
            }
            TestStatus::Timeout => {
                println!("Test {} timed out (> 5s)", self.name);
                false
            }
        }
    }
}

#[derive(Debug)]
enum TestStatus {
    Pass,
    Fail { got: String, expected: String },
    Error(String),
    Timeout,
}

fn generate(config: Config) -> Result<(), Error> {
    let generator_path = config.generator_file();
    let test_dir = config.test_dir();

    // テストディレクトリの作成
    if !test_dir.exists() {
        std::fs::create_dir_all(&test_dir)?;
    }

    if !generator_path.exists() {
        // ジェネレータファイルが存在しない場合は作成
        std::fs::write(&generator_path, config.language.generator_template())?;
        println!("Created generator file: {:?}", generator_path);
        println!("次回同じコマンドを実行するとテストケースが生成されます");
        return Ok(());
    }

    // 既存のカスタムケースを削除
    for entry in std::fs::read_dir(&test_dir)? {
        let entry = entry?;
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if name.starts_with("custom-") && (name.ends_with(".in") || name.ends_with(".out")) {
            std::fs::remove_file(entry.path())?;
        }
    }

    let input_path = test_dir.join("custom-1.in");
    let output_path = test_dir.join("custom-1.out");

    // ジェネレータの準備と実行
    let runtime = tokio::runtime::Runtime::new()
        .map_err(|e| Error::test_execution(format!("Failed to create runtime: {}", e)))?;

    runtime.block_on(async {
        match config.language {
            Language::Rust => {
                // コンパイル
                let (stdout, stderr) = docker::execute_program("rustc", &[
                    generator_path.to_str().unwrap(),
                    "-o",
                    "generator"
                ], None).await?;

                if !stderr.is_empty() {
                    return Err(Error::TestExecution(format!("Compilation failed: {}", stderr)));
                }

                // 実行
                let (stdout, stderr) = docker::execute_program("./generator", &[], None).await?;
                std::fs::write(&input_path, stdout)?;
                std::fs::write(&output_path, stderr)?;
            }
            Language::PyPy => {
                let (stdout, stderr) = docker::execute_program("pypy3", &[
                    generator_path.to_str().unwrap()
                ], None).await?;
                std::fs::write(&input_path, stdout)?;
                std::fs::write(&output_path, stderr)?;
            }
        }
        Ok(())
    })?;

    println!("Generated test case in:");
    println!("  Input:  {:?}", input_path);
    println!("  Output: {:?}", output_path);
    
    Ok(())
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
            let config = config.clone();
            handles.push(tokio::spawn(async move {
                execute_test(&config, test_case).await
            }));
        }

        // Collect results
        let mut all_passed = true;
        for handle in handles {
            let result = handle.await.map_err(|e| Error::TestExecution(e.to_string()))?;
            if !result.display() {
                all_passed = false;
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

async fn execute_test(config: &Config, test_case: TestCase) -> TestResult {
    let start = std::time::Instant::now();
    
    // コンパイルと実行
    let result = match config.language {
        Language::Rust => {
            // コンパイル
            match docker::execute_program("rustc", &[
                config.problem_file().to_str().unwrap(),
                "-o",
                "problem"
            ], None).await {
                Ok((_, stderr)) if !stderr.is_empty() => {
                    return TestResult::error(test_case.name, format!("Compilation failed: {}", stderr), start);
                }
                Err(e) => {
                    return TestResult::error(test_case.name, format!("Compilation failed: {}", e), start);
                }
                Ok(_) => {
                    // 実行
                    docker::execute_program("./problem", &[], Some(test_case.input)).await
                }
            }
        }
        Language::PyPy => {
            docker::execute_program("pypy3", &[
                config.problem_file().to_str().unwrap()
            ], Some(test_case.input)).await
        }
    };

    match result {
        Ok((got, _)) => {
            let status = if got.trim() == test_case.expected.trim() {
                TestStatus::Pass
            } else {
                TestStatus::Fail {
                    got,
                    expected: test_case.expected,
                }
            };
            TestResult::new(test_case.name, status, start.elapsed())
        }
        Err(Error::TestTimeout) => {
            TestResult::new(test_case.name, TestStatus::Timeout, Duration::from_secs(5))
        }
        Err(e) => TestResult::error(test_case.name, e.to_string(), start),
    }
}
