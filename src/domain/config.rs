use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

/// Core configuration value types
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ConfigValue {
    String(String),
    Integer(i64),
    Float(f64),
    Boolean(bool),
    Array(Vec<ConfigValue>),
    Object(HashMap<String, ConfigValue>),
}

/// Configuration node for hierarchical configuration management
#[derive(Debug, Clone)]
pub struct ConfigNode {
    pub key: String,
    pub value: Option<ConfigValue>,
    pub children: HashMap<String, ConfigNode>,
}

impl ConfigNode {
    /// Create a new configuration node
    pub fn new(key: String) -> Self {
        Self {
            key,
            value: None,
            children: HashMap::new(),
        }
    }

    /// Insert a configuration value at the specified path
    pub fn insert(&mut self, path: &[&str], value: ConfigValue) {
        if path.is_empty() {
            self.value = Some(value);
            return;
        }

        let key = path[0];
        let child = self.children.entry(key.to_string()).or_insert_with(|| ConfigNode::new(key.to_string()));
        child.insert(&path[1..], value);
    }

    /// Get a configuration value from the specified path
    pub fn get(&self, path: &[&str]) -> Option<&ConfigValue> {
        if path.is_empty() {
            return self.value.as_ref();
        }

        let key = path[0];
        
        // Try exact match first
        if let Some(child) = self.children.get(key) {
            return child.get(&path[1..]);
        }
        
        // Try wildcard match
        if let Some(child) = self.children.get("*") {
            return child.get(&path[1..]);
        }
        
        None
    }
}

/// Main configuration structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Contest configuration
    pub contest: ContestConfig,
    /// Language configuration
    pub language: LanguageConfig,
    /// Command configuration
    pub commands: CommandConfig,
    /// Output configuration
    pub output: OutputConfig,
}

/// Contest-related configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContestConfig {
    pub current_path: PathBuf,
    pub stock_path: PathBuf,
    pub template_path: PathBuf,
    pub temp_path: PathBuf,
    pub workspace_path: PathBuf,
}

/// Language-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguageConfig {
    pub language_id: String,
    pub source_file_name: String,
    pub run_command: String,
    pub compile_command: Option<String>,
    pub file_patterns: FilePatterns,
}

/// File patterns for different file types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FilePatterns {
    pub test_files: Vec<String>,
    pub contest_files: Vec<String>,
    pub build_artifacts: Vec<String>,
}

/// Command configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandConfig {
    pub open: CommandDefinition,
    pub test: CommandDefinition,
    pub submit: CommandDefinition,
    pub init: CommandDefinition,
}

/// Individual command definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandDefinition {
    pub aliases: Vec<String>,
    pub parallel: bool,
    pub steps: Vec<StepDefinition>,
}

/// Step definition for command execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepDefinition {
    pub name: String,
    pub step_type: StepType,
    pub when: Option<String>,
    pub allow_failure: bool,
}

/// Types of steps that can be executed
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StepType {
    Copy { from: String, to: String },
    Shell { command: String },
    Python { script: String },
    Test { pattern: String },
    Oj { command: String },
    MoveTree { from: String, to: String },
}

/// Output configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputConfig {
    pub preset: OutputPreset,
    pub format: OutputFormat,
}

/// Output preset levels
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OutputPreset {
    Quiet,
    SummaryOnly,
    MinimalDetails,
    Verbose,
}

/// Output format options
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OutputFormat {
    Minimal,
    Standard,
    Competitive,
    Compact,
}

/// Configuration template context for variable expansion
#[derive(Debug, Clone)]
pub struct ConfigContext {
    pub contest_name: Option<String>,
    pub problem_name: Option<String>,
    pub language: Option<String>,
    pub custom: HashMap<String, String>,
}

impl ConfigContext {
    pub fn new() -> Self {
        Self {
            contest_name: None,
            problem_name: None,
            language: None,
            custom: HashMap::new(),
        }
    }

    /// Expand template strings with context values
    pub fn expand(&self, template: &str) -> String {
        let mut result = template.to_string();
        
        if let Some(contest) = &self.contest_name {
            result = result.replace("{contest_name}", contest);
        }
        
        if let Some(problem) = &self.problem_name {
            result = result.replace("{problem_name}", problem);
        }
        
        if let Some(language) = &self.language {
            result = result.replace("{language}", language);
        }
        
        for (key, value) in &self.custom {
            result = result.replace(&format!("{{{key}}}"), value);
        }
        
        result
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            contest: ContestConfig {
                current_path: PathBuf::from("."),
                stock_path: PathBuf::from("./contests"),
                template_path: PathBuf::from("./templates"),
                temp_path: PathBuf::from("./tmp"),
                workspace_path: PathBuf::from("./workspace"),
            },
            language: LanguageConfig {
                language_id: "rust".to_string(),
                source_file_name: "main.rs".to_string(),
                run_command: "cargo run".to_string(),
                compile_command: Some("cargo build --release".to_string()),
                file_patterns: FilePatterns {
                    test_files: vec!["*.txt".to_string(), "test_*.txt".to_string()],
                    contest_files: vec!["*.rs".to_string(), "Cargo.toml".to_string()],
                    build_artifacts: vec!["target/".to_string()],
                },
            },
            commands: CommandConfig {
                open: CommandDefinition {
                    aliases: vec!["o".to_string()],
                    parallel: false,
                    steps: vec![],
                },
                test: CommandDefinition {
                    aliases: vec!["t".to_string()],
                    parallel: true,
                    steps: vec![],
                },
                submit: CommandDefinition {
                    aliases: vec!["s".to_string()],
                    parallel: false,
                    steps: vec![],
                },
                init: CommandDefinition {
                    aliases: vec!["i".to_string()],
                    parallel: false,
                    steps: vec![],
                },
            },
            output: OutputConfig {
                preset: OutputPreset::MinimalDetails,
                format: OutputFormat::Competitive,
            },
        }
    }
}