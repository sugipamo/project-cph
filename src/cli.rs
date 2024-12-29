use std::path::{Path, PathBuf};
use clap::{Parser, Subcommand, Command, ArgMatches, error::ErrorKind};
use serde::{Serialize, Deserialize};
use thiserror::Error;
use crate::{
    Language, 
    error::Result, 
    workspace::{Workspace, Config}, 
    oj::OJContainer, 
    oj::ProblemInfo,
    config::aliases::AliasConfig,
};

#[derive(Debug, Error)]
pub enum CliError {
    #[error("サイト '{0}' は存在しません。利用可能なサイト: atcoder")]
    UnknownSite(String),

    #[error("コマンド '{0}' は存在しません。利用可能なコマンド: work, test, language, open, submit, generate, login")]
    UnknownCommand(String),

    #[error("引数 '{0}' が必要です")]
    MissingArgument(&'static str),

    #[error("言語 '{0}' は無効です")]
    InvalidLanguage(String),

    #[error("エイリアスの解決に失敗しました: {0}")]
    AliasResolutionError(String),

    #[error("コマンドが指定されていません")]
    MissingCommand,

    #[error("サブコマンドが指定されていません")]
    MissingSubcommand,
}

impl From<CliError> for clap::Error {
    fn from(err: CliError) -> Self {
        let msg = err.to_string();
        match err {
            CliError::UnknownSite(_) => 
                clap::Error::raw(ErrorKind::UnknownArgument, msg),
            CliError::UnknownCommand(_) => 
                clap::Error::raw(ErrorKind::UnknownArgument, msg),
            CliError::MissingArgument(_) => 
                clap::Error::raw(ErrorKind::MissingRequiredArgument, msg),
            CliError::InvalidLanguage(_) => 
                clap::Error::raw(ErrorKind::InvalidValue, msg),
            CliError::AliasResolutionError(_) => 
                clap::Error::raw(ErrorKind::InvalidValue, msg),
            CliError::MissingCommand => 
                clap::Error::raw(ErrorKind::MissingSubcommand, msg),
            CliError::MissingSubcommand => 
                clap::Error::raw(ErrorKind::MissingSubcommand, msg),
        }
    }
}

/// コマンドライン引数の解析を行う構造体
#[derive(Debug)]
pub struct CliParser {
    alias_config: AliasConfig,
}

impl CliParser {
    pub fn new(alias_config: AliasConfig) -> Self {
        Self { alias_config }
    }

    /// コマンドライン引数を解析します
    pub fn parse_from_args(&self, args: Vec<String>) -> clap::error::Result<ArgMatches> {
        // 最初の引数（プログラム名）以外を小文字に変換
        let args: Vec<String> = args.into_iter()
            .enumerate()
            .map(|(i, s)| if i == 0 { s } else { s.to_lowercase() })
            .collect();

        // エイリアス解決
        let resolved_args = self.alias_config.resolve_args(args)
            .ok_or_else(|| CliError::AliasResolutionError(
                "コマンドまたはエイリアスの解決に失敗しました".to_string()
            ))?;

        self.build_cli().try_get_matches_from(resolved_args)
            .map_err(|e| {
                // clapのエラーメッセージを日本語化
                let msg = match e.kind() {
                    ErrorKind::MissingRequiredArgument => "必要な引数が指定されていません",
                    ErrorKind::UnknownArgument => "不明な引数が指定されています",
                    ErrorKind::InvalidValue => "無効な値が指定されています",
                    ErrorKind::MissingSubcommand => "サブコマンドが指定されていません",
                    _ => return e,
                };
                clap::Error::raw(e.kind(), msg.to_string())
            })
    }

    /// CLIの構造を構築します
    fn build_cli(&self) -> Command {
        Command::new("cph")
            .about("競技プログラミングヘルパー")
            .subcommand_required(true)
            .subcommand(
                Command::new("atcoder")
                    .aliases(&["at-coder", "at_coder", "ac"])
                    .about("AtCoder関連のコマンド")
                    .subcommand_required(true)
                    .subcommands(self.common_subcommands())
            )
    }

    /// 問題IDが有効かどうかを確認します
    fn is_valid_problem_id(s: &str) -> bool {
        if s.is_empty() {
            return false;
        }
        let s = s.to_lowercase();
        let valid_ids = ["a", "b", "c", "d", "e", "f", "g", "ex"];
        valid_ids.contains(&s.as_str())
    }

    /// コンテストIDが有効かどうかを確認します
    fn is_valid_contest_id(s: &str) -> bool {
        if s.is_empty() {
            return false;
        }
        let s = s.to_lowercase();
        if s.len() < 4 {
            return false;
        }
        let prefix = &s[..3];
        let valid_prefixes = ["abc", "arc", "agc"];
        if !valid_prefixes.contains(&prefix) {
            return false;
        }
        s[3..].chars().all(|c| c.is_ascii_digit())
    }

    /// 共通のサブコマンドを構築します
    fn common_subcommands(&self) -> Vec<Command> {
        vec![
            Command::new("work")
                .aliases(&["w"])
                .about("コンテストのワークスペースを設定")
                .arg(clap::Arg::new("contest")
                    .help("コンテストID")
                    .required(true)
                    .allow_hyphen_values(true)
                    .value_parser(|s: &str| {
                        if !Self::is_valid_contest_id(s) {
                            return Err(String::from("無効なコンテストID形式です"));
                        }
                        Ok(s.to_string())
                    })),
            Command::new("test")
                .aliases(&["t", "check"])
                .about("問題のテストを実行")
                .arg(clap::Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)
                    .allow_hyphen_values(true)
                    .value_parser(|s: &str| {
                        // 空白を含む場合は最初の部分だけを検証
                        let id = s.split_whitespace().next().unwrap_or(s);
                        if !Self::is_valid_problem_id(id) {
                            return Err(String::from("無効な問題IDです"));
                        }
                        Ok(s.to_string())
                    })),
            Command::new("language")
                .aliases(&["l", "lang"])
                .about("使用する言語を設定")
                .arg(clap::Arg::new("language")
                    .help("プログラミング言語")
                    .required(true)
                    .allow_hyphen_values(true)
                    .value_parser(|s: &str| {
                        // 言語名を小文字に変換して検証
                        let lang = s.to_lowercase();
                        let valid_langs = [
                            "python", "python3", "py",
                            "cpp", "c++",
                            "rust", "rs",
                        ];
                        if !valid_langs.contains(&lang.as_str()) {
                            return Err(format!("無効な言語指定です: {}", s));
                        }
                        Ok(s.to_string())
                    })),
            Command::new("open")
                .aliases(&["o"])
                .about("問題ページを開く")
                .arg(clap::Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)
                    .allow_hyphen_values(true)),
            Command::new("submit")
                .aliases(&["s", "sub"])
                .about("解答を提出")
                .arg(clap::Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)
                    .allow_hyphen_values(true)),
            Command::new("generate")
                .aliases(&["g"])
                .about("テンプレートを生成")
                .arg(clap::Arg::new("problem_id")
                    .help("問題ID")
                    .required(true)
                    .allow_hyphen_values(true)),
            Command::new("login")
                .aliases(&["auth"])
                .about("サイトにログイン"),
        ]
    }
}

#[derive(Debug, Parser)]
#[command(name = "cph")]
pub struct Cli {
    #[command(subcommand)]
    pub site: Site,
}

#[derive(Debug, Subcommand, Clone)]
pub enum Site {
    #[command(name = "atcoder", alias = "at-coder", alias = "at_coder")]
    AtCoder {
        #[command(subcommand)]
        command: CommonSubCommand,
    },
}

impl Site {
    pub fn get_url(&self) -> &'static str {
        match self {
            Site::AtCoder { .. } => "https://atcoder.jp",
        }
    }

    pub fn get_name(&self) -> &'static str {
        match self {
            Site::AtCoder { .. } => "AtCoder",
        }
    }

    pub fn get_problem_url(&self, contest: &str, problem_id: &str) -> String {
        match self {
            Site::AtCoder { .. } => format!(
                "https://atcoder.jp/contests/{}/tasks/{}_{}",
                contest,
                contest,
                problem_id
            ),
        }
    }
}

impl From<&str> for Site {
    fn from(s: &str) -> Self {
        match s {
            "atcoder" => Site::AtCoder { command: default_command() },
            _ => panic!("Unknown site: {}", s),
        }
    }
}

impl<'de> Deserialize<'de> for Site {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Ok(Site::from(s.as_str()))
    }
}

impl Serialize for Site {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match self {
            Site::AtCoder { .. } => serializer.serialize_str("atcoder"),
        }
    }
}

fn default_command() -> CommonSubCommand {
    CommonSubCommand::Work { contest: String::new() }
}

#[derive(Debug, Subcommand, Clone, Serialize, Deserialize)]
pub enum CommonSubCommand {
    #[command(name = "work")]
    Work {
        contest: String,
    },
    #[command(name = "test")]
    Test {
        problem_id: String,
    },
    #[command(name = "language")]
    Language {
        language: Language,
    },
    #[command(name = "open")]
    Open {
        problem_id: String,
    },
    #[command(name = "submit")]
    Submit {
        problem_id: String,
    },
    #[command(name = "generate")]
    Generate {
        problem_id: String,
    },
    #[command(name = "login")]
    Login,
}

impl Cli {
    /// エイリアス設定を使用してコマンドライン引数を解析します
    pub fn parse_from(args: Vec<String>, alias_config: AliasConfig) -> clap::error::Result<Self> {
        let parser = CliParser::new(alias_config);
        let matches = parser.parse_from_args(args)?;
        Self::from_matches(&matches)
    }

    /// ArgMatchesからCliインスタンスを構築します
    fn from_matches(matches: &ArgMatches) -> clap::error::Result<Self> {
        // サイトの解決
        let (site_name, site_matches) = matches.subcommand()
            .ok_or_else(|| CliError::MissingSubcommand)?;

        // サブコマンドの解決
        let (cmd_name, cmd_matches) = site_matches.subcommand()
            .ok_or_else(|| CliError::MissingCommand)?;

        // コマンドの構築
        let command = match cmd_name {
            "work" => CommonSubCommand::Work {
                contest: cmd_matches.get_one::<String>("contest")
                    .ok_or_else(|| CliError::MissingArgument("contest"))?
                    .clone(),
            },
            "test" => CommonSubCommand::Test {
                problem_id: cmd_matches.get_one::<String>("problem_id")
                    .ok_or_else(|| CliError::MissingArgument("problem_id"))?
                    .clone(),
            },
            "language" => {
                let lang_str = cmd_matches.get_one::<String>("language")
                    .ok_or_else(|| CliError::MissingArgument("language"))?;
                CommonSubCommand::Language {
                    language: lang_str.parse()
                        .map_err(|_| CliError::InvalidLanguage(lang_str.clone()))?
                }
            },
            "open" => CommonSubCommand::Open {
                problem_id: cmd_matches.get_one::<String>("problem_id")
                    .ok_or_else(|| CliError::MissingArgument("problem_id"))?
                    .clone(),
            },
            "submit" => CommonSubCommand::Submit {
                problem_id: cmd_matches.get_one::<String>("problem_id")
                    .ok_or_else(|| CliError::MissingArgument("problem_id"))?
                    .clone(),
            },
            "generate" => CommonSubCommand::Generate {
                problem_id: cmd_matches.get_one::<String>("problem_id")
                    .ok_or_else(|| CliError::MissingArgument("problem_id"))?
                    .clone(),
            },
            "login" => CommonSubCommand::Login,
            _ => return Err(CliError::UnknownCommand(cmd_name.to_string()).into()),
        };

        // サイトの構築
        let site = match site_name {
            "atcoder" => Site::AtCoder { command },
            _ => return Err(CliError::UnknownSite(site_name.to_string()).into()),
        };

        Ok(Self { site })
    }

    pub async fn execute(self) -> Result<()> {
        match self.site {
            Site::AtCoder { command } => command.execute().await,
        }
    }
}

impl CommonSubCommand {
    pub async fn execute(&self) -> Result<()> {
        match self {
            CommonSubCommand::Work { contest } => {
                let mut workspace = Workspace::new()?;
                let current_contest = workspace.get_current_config().map(|c| c.contest.clone()).unwrap_or_default();
                if !current_contest.is_empty() && current_contest == *contest {
                    println!("Already in contest {}", contest);
                    return Ok(());
                }
                workspace.set_workspace(contest, Site::AtCoder { command: CommonSubCommand::Work { contest: contest.clone() } })?;
                println!("Successfully set up workspace for contest {}", contest);
                Ok(())
            }
            CommonSubCommand::Test { problem_id } => {
                let workspace = Workspace::new()?;
                let config = workspace.load_config()?;
                let result = run_test(&workspace.get_workspace_dir(), problem_id, &config).await?;
                if result {
                    println!("All tests passed!");
                }
                Ok(())
            }
            CommonSubCommand::Language { language } => {
                let mut workspace = Workspace::new()?;
                workspace.set_language(*language)?;
                println!("Language set to {}", language);
                Ok(())
            }
            CommonSubCommand::Open { problem_id } => {
                let mut workspace = Workspace::new()?;
                let config = workspace.load_config()?;
                
                // 問題URLの生成
                let url = format!(
                    "https://atcoder.jp/contests/{}/tasks/{}_{}",
                    config.contest,
                    config.contest,
                    problem_id
                );

                // ソースファイルの準備
                let path = workspace.setup_problem(problem_id)?;
                
                // テストケースのダウンロード
                let oj = OJContainer::new(workspace.get_workspace_dir())?;
                oj.ensure_image().await?;
                
                let problem = ProblemInfo {
                    url: url.clone(),
                    source_path: path.clone(),
                    problem_id: problem_id.to_string(),
                };
                
                oj.open(problem).await?;
                
                println!("Problem setup completed for {}", path.display());
                Ok(())
            }
            CommonSubCommand::Submit { problem_id } => {
                let mut workspace = Workspace::new()?;
                let config = workspace.load_config()?;
                
                // 問題URLの生成
                let url = config.site.get_problem_url(&config.contest, &problem_id);
                
                // ソースファイルの準備
                let path = workspace.setup_problem(&problem_id)?;
                
                let problem = ProblemInfo {
                    url,
                    source_path: path.clone(),
                    problem_id: problem_id.to_string(),
                };

                let language_id = config.language.get_id(&config.site);
                let oj = OJContainer::new(workspace.get_workspace_dir())?;
                oj.ensure_image().await?;
                oj.submit(&problem, &config.site, language_id).await
            }
            CommonSubCommand::Generate { problem_id: _ } => {
                println!("Generate command is not implemented yet");
                Ok(())
            }
            CommonSubCommand::Login => {
                println!("Logging in...");
                let workspace = Workspace::new()?;
                let config = workspace.load_config()?;
                let oj = OJContainer::new(workspace.get_workspace_dir())?;
                oj.ensure_image().await?;
                oj.login(&config.site).await
            }
        }
    }
}

async fn run_test(_workspace_dir: &Path, problem_id: &str, config: &Config) -> Result<bool> {
    let mut workspace = Workspace::new()?;
    let problem_path = workspace.setup_problem(problem_id)?;

    // テストケースの存在確認
    if !has_valid_test_cases(&problem_path)? {
        println!("No test cases found.");
        return Ok(true);
    }

    // テストの実行
    let test_config = Config {
        language: config.language,
        site: config.site.clone(),
        contest: config.contest.clone(),
    };

    crate::test::run(test_config, problem_id).await
}

// テストケースが有効かどうかを確認
fn has_valid_test_cases(problem_dir: &PathBuf) -> Result<bool> {
    if !problem_dir.exists() {
        return Ok(false);
    }

    // 少なくとも1つの.inファイルと対応する.outファイルが存在するか確認
    let entries = std::fs::read_dir(problem_dir)?;
    let mut has_input = false;
    let mut has_output = false;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if let Some(extension) = path.extension() {
            if extension == "in" {
                has_input = true;
            } else if extension == "out" {
                has_output = true;
            }
        }
    }

    Ok(has_input && has_output)
} 