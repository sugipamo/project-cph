use std::path::{PathBuf, Path};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

pub mod docker;
pub mod test;
pub mod error;

pub use error::{Error, Result, InputError, DockerError};

// 共通の定数
pub const TEST_FILE_EXTENSIONS: [&str; 2] = [".in", ".out"];
pub const CUSTOM_TEST_PREFIX: &str = "custom-";
pub const DEFAULT_TIMEOUT_SECS: u64 = 5;
pub const DEFAULT_MEMORY_LIMIT: &str = "512m";

// エラーメッセージの定数
pub const INVALID_LANGUAGE_ERROR: &str = "Invalid language";
pub const INVALID_COMMAND_ERROR: &str = "Invalid command";

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

// ファイル操作のトレイトを定義
trait FileOps {
    fn ensure_directory(&self, path: &Path) -> Result<()>;
    fn write_file(&self, path: &Path, content: &str, message: &str) -> Result<()>;
}

impl FileOps for Config {
    fn ensure_directory(&self, path: &Path) -> Result<()> {
        if !path.exists() {
            std::fs::create_dir_all(path)?;
        }
        Ok(())
    }

    fn write_file(&self, path: &Path, content: &str, message: &str) -> Result<()> {
        if let Some(parent) = path.parent() {
            self.ensure_directory(parent)?;
        }
        std::fs::write(path, content)?;
        println!("{}: {:?}", message, path);
        Ok(())
    }
}

impl Config {
    // create_fileとcopy_fileを新しいwrite_fileメソッドを使用するように変更
    fn create_file(&self, path: &Path, content: &str) -> Result<()> {
        self.write_file(path, content, "Created file")
    }

    fn copy_file(&self, from: &Path, to: &Path) -> Result<()> {
        let content = std::fs::read_to_string(from)?;
        self.write_file(to, &content, "Created file from template")
    }
}

// 言語設定を構造体として定義
#[derive(Debug, Clone)]
struct LanguageConfig {
    extension: &'static str,
    template_name: &'static str,
    default_content: &'static str,
    generator_template: &'static str,
    docker_image: &'static str,
    command: &'static str,
    compile_command: Option<&'static str>,
}

impl Language {
    const RUST_CONFIG: LanguageConfig = LanguageConfig {
        extension: "rs",
        template_name: "main.rs",
        default_content: include_str!("templates/template/main.rs"),
        generator_template: include_str!("templates/template/generator.rs"),
        docker_image: "rust:1.70",
        command: "rustc",
        compile_command: Some("rustc"),
    };

    const PYPY_CONFIG: LanguageConfig = LanguageConfig {
        extension: "py",
        template_name: "main.py",
        default_content: include_str!("templates/template/main.py"),
        generator_template: include_str!("templates/template/generator.py"),
        docker_image: "pypy:3.10",
        command: "python",
        compile_command: None,
    };

    fn config(&self) -> &'static LanguageConfig {
        match self {
            Language::Rust => &Self::RUST_CONFIG,
            Language::PyPy => &Self::PYPY_CONFIG,
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

    pub fn docker_image(&self) -> &str {
        self.config().docker_image
    }

    pub fn command(&self) -> &str {
        self.config().command
    }

    // 言語固有の実行コマンドを生成
    fn get_execution_commands(&self, path: &Path) -> Vec<(String, Vec<String>)> {
        let config = self.config();
        let path_str = path.to_str().unwrap().to_string();
        
        match self {
            Language::Rust => {
                vec![
                    ("rustc".to_string(), vec![path_str.clone(), "-o".to_string(), "program".to_string()]),
                    ("./program".to_string(), vec![]),
                ]
            },
            Language::PyPy => {
                vec![
                    ("pypy3".to_string(), vec![path_str]),
                ]
            },
        }
    }
}

impl TryFrom<&str> for Language {
    type Error = error::Error;

    fn try_from(s: &str) -> error::Result<Self> {
        match s.to_lowercase().as_str() {
            "rust" | "r" => Ok(Language::Rust),
            "pypy" | "py" => Ok(Language::PyPy),
            _ => Err(error::Error::Input(error::InputError::InvalidValue {
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
    type Error = error::Error;

    fn try_from(s: &str) -> error::Result<Self> {
        match s.to_lowercase().as_str() {
            "open" | "o" => Ok(Command::Open),
            "test" | "t" => Ok(Command::Test),
            "submit" | "s" => Ok(Command::Submit),
            "generate" | "g" => Ok(Command::Generate),
            _ => Err(error::Error::Input(error::InputError::InvalidValue {
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

    fn read_contest_info(&self) -> Result<ContestInfo> {
        let info_path = self.contest_info_path();
        if info_path.exists() {
            let contents = std::fs::read_to_string(&info_path)?;
            serde_yaml::from_str(&contents)
                .map_err(|e| Error::Input(InputError::Format(format!("Failed to parse contest info: {}", e))))
        } else {
            Ok(ContestInfo::default())
        }
    }

    fn write_contest_info(&self, info: &ContestInfo) -> Result<()> {
        let info_path = self.contest_info_path();
        self.ensure_directory(info_path.parent().unwrap())?;
        let yaml = serde_yaml::to_string(info)
            .map_err(|e| Error::Input(InputError::Format(format!("Failed to serialize contest info: {}", e))))?;
        std::fs::write(&info_path, yaml)?;
        Ok(())
    }

    fn ensure_contest_exists(&self) -> Result<()> {
        let mut info = self.read_contest_info()?;
        info.contests.entry(self.contest_id.clone())
            .or_default();
        self.write_contest_info(&info)
    }

    fn update_problem_info(&self, has_generator: bool) -> Result<()> {
        let mut info = self.read_contest_info()?;
        let contest = info.contests.entry(self.contest_id.clone()).or_default();
        let problem = contest.problems.entry(self.problem_id.clone()).or_default();
        
        problem.solution = Some(self.get_file_name(&self.problem_id, None));
        if has_generator {
            problem.generator = Some(self.get_file_name(&self.problem_id, Some("gen")));
        }

        self.write_contest_info(&info)
    }

    async fn execute_program(&self, cmd: &str, args: &[&str]) -> Result<(String, String)> {
        let (stdout, stderr) = docker::execute_program(cmd, args, None).await?;
        
        match cmd {
            // rustcの場合、エラーメッセージに "error" が含まれているかチェック
            "rustc" if stderr.contains("error") => {
                Err(Error::Runtime(format!("Compilation failed:\n{}", stderr)))
            }
            // PyPyの場合、エラーメッセージに特定のパターンが含まれているかチェック
            "pypy3" if stderr.contains("Error") || stderr.contains("Exception") => {
                Err(Error::Runtime(format!("Execution failed:\n{}", stderr)))
            }
            // 実行ファイルの場合は終了コードで判断（stderrは警告やデバッグ情報の可能性あり）
            cmd if cmd.starts_with("./") => Ok((stdout, stderr)),
            // その他の場合は正常として扱う
            _ => Ok((stdout, stderr))
        }
    }

    async fn write_test_case(&self, input_path: &Path, output_path: &Path, stdout: String, stderr: String) -> Result<()> {
        std::fs::write(input_path, stdout)?;
        std::fs::write(output_path, stderr)?;
        println!("Generated test case in:");
        println!("  Input:  {:?}", input_path);
        println!("  Output: {:?}", output_path);
        Ok(())
    }

    async fn generate_test_case(&self, generator_path: &Path, input_path: &Path, output_path: &Path) -> Result<()> {
        let commands = self.language.get_execution_commands(generator_path);
        
        for (cmd, args) in commands {
            let (stdout, stderr) = self.execute_program(&cmd, &args.iter().map(|s| s.as_str()).collect::<Vec<_>>()).await?;
            
            if cmd.starts_with("./") || cmd == "pypy3" {
                self.write_test_case(input_path, output_path, stdout, stderr).await?;
            }
        }
        
        Ok(())
    }
}

fn create_runtime() -> Result<tokio::runtime::Runtime> {
    tokio::runtime::Runtime::new()
        .map_err(|e| Error::Runtime(format!("Failed to create runtime: {}", e)))
}

fn run_async<F, T>(future: F) -> Result<T>
where
    F: std::future::Future<Output = Result<T>>,
{
    let runtime = create_runtime()?;
    runtime.block_on(future)
}

pub fn run(config: Config) -> Result<()> {
    match config.command {
        Command::Open => open(config),
        Command::Test => test::run(config),
        Command::Submit => submit(config),
        Command::Generate => generate(config),
    }
}

fn open(config: Config) -> Result<()> {
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

fn generate(config: Config) -> Result<()> {
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

    run_async(async {
        config.generate_test_case(&generator_path, &input_path, &output_path).await
    })
}

fn submit(_config: Config) -> Result<()> {
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
