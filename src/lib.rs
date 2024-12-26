use std::path::{PathBuf, Path};
use thiserror::Error;
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

pub mod docker;
pub mod test;

// 共通の定数
pub const TEST_FILE_EXTENSIONS: [&str; 2] = [".in", ".out"];
pub const CUSTOM_TEST_PREFIX: &str = "custom-";
pub const DEFAULT_TIMEOUT_SECS: u64 = 5;
pub const DEFAULT_MEMORY_LIMIT: &str = "512m";

// Docker関連の定数
pub const DEFAULT_RUST_IMAGE: &str = "rust:1.70";
pub const DEFAULT_PYPY_IMAGE: &str = "pypy:3.10";

#[derive(Debug, Error)]
pub enum Error {
    #[error("Invalid input: {0}")]
    Input(#[from] InputError),
    
    #[error("Test error: {0}")]
    Test(#[from] test::TestError),
    
    #[error("Docker error: {0}")]
    Docker(#[from] docker::DockerError),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

#[derive(Debug, Error)]
pub enum InputError {
    #[error("Invalid {kind}: {value}")]
    InvalidValue { kind: &'static str, value: String },
    
    #[error("Missing {0}")]
    Missing(&'static str),
    
    #[error("Invalid format: {0}")]
    Format(String),
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

#[derive(Debug, Clone)]
struct LanguageConfig {
    extension: &'static str,
    template_name: &'static str,
    default_content: &'static str,
    generator_template: &'static str,
}

impl Language {
    fn config(&self) -> LanguageConfig {
        match self {
            Language::Rust => LanguageConfig {
                extension: "rs",
                template_name: "main.rs",
                default_content: "fn main() {\n    \n}\n",
                generator_template: r#"fn generate_case() -> (String, String) {
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
            },
            Language::PyPy => LanguageConfig {
                extension: "py",
                template_name: "main.py",
                default_content: "def main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
                generator_template: r#"def generate_case():
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
            },
        }
    }

    pub fn extension(&self) -> &str {
        self.config().extension
    }

    pub fn template_name(&self) -> &str {
        self.config().template_name
    }

    pub fn default_content(&self) -> &str {
        self.config().default_content
    }

    pub fn generator_template(&self) -> &str {
        self.config().generator_template
    }
}

impl TryFrom<&str> for Language {
    type Error = Error;

    fn try_from(s: &str) -> Result<Self, Self::Error> {
        match s.to_lowercase().as_str() {
            "rust" | "r" => Ok(Language::Rust),
            "pypy" | "py" => Ok(Language::PyPy),
            _ => Err(Error::Input(InputError::InvalidValue {
                kind: "language",
                value: s.to_string(),
            })),
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
            _ => Err(Error::Input(InputError::InvalidValue {
                kind: "command",
                value: s.to_string(),
            })),
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

    fn get_file_name(&self, prefix: &str, suffix: Option<&str>) -> String {
        let base = if let Some(suffix) = suffix {
            format!("{}_{}", prefix, suffix)
        } else {
            prefix.to_string()
        };
        format!("{}.{}", base, self.language.extension())
    }

    pub fn contest_dir(&self) -> PathBuf {
        self.workspace_dir
            .join(self.contest_type().as_str())
    }

    pub fn problem_file(&self) -> PathBuf {
        self.contest_dir()
            .join(self.get_file_name(&self.problem_id, None))
    }

    pub fn generator_file(&self) -> PathBuf {
        self.contest_dir()
            .join(self.get_file_name(&self.problem_id, Some("gen")))
    }

    pub fn template_path(&self) -> PathBuf {
        self.contest_dir()
            .join("template")
            .join(self.language.template_name())
    }

    pub fn test_dir(&self) -> PathBuf {
        self.contest_dir()
            .join("test")
            .join(&self.problem_id)
    }

    pub fn contest_info_path(&self) -> PathBuf {
        self.contest_dir()
            .join("contests.yaml")
    }

    fn is_test_file(name: &str) -> bool {
        TEST_FILE_EXTENSIONS.iter().any(|ext| name.ends_with(ext))
    }

    fn is_custom_test_file(name: &str) -> bool {
        name.starts_with(CUSTOM_TEST_PREFIX) && Self::is_test_file(name)
    }

    fn ensure_directory(&self, path: &Path) -> Result<(), Error> {
        if !path.exists() {
            std::fs::create_dir_all(path)?;
        }
        Ok(())
    }

    fn create_file(&self, path: &Path, content: &str) -> Result<(), Error> {
        if let Some(parent) = path.parent() {
            self.ensure_directory(parent)?;
        }
        std::fs::write(path, content)?;
        println!("Created file: {:?}", path);
        Ok(())
    }

    fn copy_file(&self, from: &Path, to: &Path) -> Result<(), Error> {
        if let Some(parent) = to.parent() {
            self.ensure_directory(parent)?;
        }
        std::fs::copy(from, to)?;
        println!("Created file from template: {:?}", to);
        Ok(())
    }

    fn read_contest_info(&self) -> Result<ContestInfo, Error> {
        let info_path = self.contest_info_path();
        if info_path.exists() {
            let contents = std::fs::read_to_string(&info_path)?;
            serde_yaml::from_str(&contents)
                .map_err(|e| Error::Input(InputError::Format(format!("Failed to parse contest info: {}", e))))
        } else {
            Ok(ContestInfo::default())
        }
    }

    fn write_contest_info(&self, info: &ContestInfo) -> Result<(), Error> {
        let info_path = self.contest_info_path();
        self.ensure_directory(info_path.parent().unwrap())?;
        let yaml = serde_yaml::to_string(info)
            .map_err(|e| Error::Input(InputError::Format(format!("Failed to serialize contest info: {}", e))))?;
        std::fs::write(&info_path, yaml)?;
        Ok(())
    }

    fn ensure_contest_exists(&self) -> Result<(), Error> {
        let mut info = self.read_contest_info()?;
        info.contests.entry(self.contest_id.clone())
            .or_default();
        self.write_contest_info(&info)
    }

    fn update_problem_info(&self, has_generator: bool) -> Result<(), Error> {
        let mut info = self.read_contest_info()?;
        let contest = info.contests.entry(self.contest_id.clone()).or_default();
        let problem = contest.problems.entry(self.problem_id.clone()).or_default();
        
        problem.solution = Some(self.get_file_name(&self.problem_id, None));
        if has_generator {
            problem.generator = Some(self.get_file_name(&self.problem_id, Some("gen")));
        }

        self.write_contest_info(&info)
    }

    async fn execute_program(&self, cmd: &str, args: &[&str]) -> Result<(String, String), Error> {
        let (stdout, stderr) = docker::execute_program(cmd, args, None).await?;
        
        // rustcの場合、エラーメッセージに "error" が含まれているかチェック
        if cmd == "rustc" && stderr.contains("error") {
            return Err(Error::Test(test::TestError::new(format!("Compilation failed:\n{}", stderr))));
        }

        // 実行ファイルの場合は終了コードで判断（stderrは警告やデバッグ情報の可能性あり）
        if cmd.starts_with("./") {
            // stderrは期待される出力として扱う
            return Ok((stdout, stderr));
        }

        // PyPyの場合、エラーメッセージに特定のパターンが含まれているかチェック
        if cmd == "pypy3" && (stderr.contains("Error") || stderr.contains("Exception")) {
            return Err(Error::Test(test::TestError::new(format!("Execution failed:\n{}", stderr))));
        }

        Ok((stdout, stderr))
    }
}

pub fn run(config: Config) -> Result<(), Error> {
    match config.command {
        Command::Open => open(config),
        Command::Test => test::run(config),
        Command::Submit => submit(config),
        Command::Generate => generate(config),
    }
}

fn open(config: Config) -> Result<(), Error> {
    let problem_file = config.problem_file();
    if problem_file.exists() {
        println!("Problem file already exists: {:?}", problem_file);
        return Ok(());
    }
    
    // Create problem file
    if config.template_path().exists() {
        config.copy_file(&config.template_path(), &problem_file)?;
    } else {
        config.create_file(&problem_file, config.language.default_content())?;
    }

    // Update contest info
    config.ensure_contest_exists()?;
    config.update_problem_info(false)?;

    Ok(())
}

fn generate(config: Config) -> Result<(), Error> {
    let generator_path = config.generator_file();
    let test_dir = config.test_dir();

    // テストディレクトリの作成
    config.ensure_directory(&test_dir)?;

    if !generator_path.exists() {
        // ジェネレータファイルが存在しない場合は作成
        config.create_file(&generator_path, config.language.generator_template())?;
        println!("次回同じコマンドを実行するとテストケースが生成されます");
        
        // Update contest info with generator
        config.ensure_contest_exists()?;
        config.update_problem_info(true)?;
        
        return Ok(());
    }

    // 既存のカスタムケースを削除
    for entry in std::fs::read_dir(&test_dir)? {
        let entry = entry?;
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if Config::is_custom_test_file(&name) {
            std::fs::remove_file(entry.path())?;
        }
    }

    let input_path = test_dir.join(format!("{}{}.in", CUSTOM_TEST_PREFIX, 1));
    let output_path = test_dir.join(format!("{}{}.out", CUSTOM_TEST_PREFIX, 1));

    // ジェネレータの準備と実行
    let runtime = tokio::runtime::Runtime::new()
        .map_err(|e| Error::Test(test::TestError::new(format!("Failed to create runtime: {}", e))))?;

    runtime.block_on(async {
        let result: Result<(), Error> = async {
            match config.language {
                Language::Rust => {
                    // コンパイル
                    config.execute_program("rustc", &[
                        generator_path.to_str().unwrap(),
                        "-o",
                        "generator"
                    ]).await?;

                    // 実行
                    let (stdout, stderr) = config.execute_program("./generator", &[]).await?;
                    std::fs::write(&input_path, stdout)?;
                    std::fs::write(&output_path, stderr)?;
                }
                Language::PyPy => {
                    let (stdout, stderr) = config.execute_program("pypy3", &[
                        generator_path.to_str().unwrap()
                    ]).await?;
                    std::fs::write(&input_path, stdout)?;
                    std::fs::write(&output_path, stderr)?;
                }
            }
            Ok(())
        }.await;
        result
    })?;

    println!("Generated test case in:");
    println!("  Input:  {:?}", input_path);
    println!("  Output: {:?}", output_path);
    
    Ok(())
}

fn submit(_config: Config) -> Result<(), Error> {
    println!("Submit command not implemented yet");
    Ok(())
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct ContestInfo {
    contests: HashMap<String, Contest>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct Contest {
    problems: HashMap<String, Problem>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct Problem {
    solution: Option<String>,
    generator: Option<String>,
}
