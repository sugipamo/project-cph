use anyhow::{Result, anyhow};
use crate::contest::model::{Command, CommandContext};

#[derive(Debug, Clone, PartialEq, Eq)]
enum TokenType {
    Site,
    Language,
    ContestId,
    ProblemId,
}

#[derive(Debug, Clone)]
struct TokenInterpretation {
    token: String,
    interpretations: Vec<(TokenType, String)>,
}

pub struct Parser {
    config: crate::contest::parse::config::Config,
}

impl Default for Parser {
    fn default() -> Self {
        Self::new()
    }
}

impl Parser {
    #[must_use = "この関数は新しいParserインスタンスを返します"]
    pub fn new() -> Self {
        Self {
            config: crate::contest::parse::config::Config::new(),
        }
    }

    #[must_use = "この関数は新しいParserインスタンスを返します"]
    pub fn with_config(config: crate::contest::parse::config::Config) -> Self {
        Self { config }
    }

    pub fn parse(&self, input: &str) -> Result<CommandContext> {
        let tokens: Vec<&str> = input.split_whitespace().collect();
        if tokens.is_empty() {
            return Err(anyhow!("入力が空です"));
        }

        let mut interpretations = Vec::new();
        for token in tokens {
            let token_interp = self.interpret_token(token)?;
            interpretations.push(token_interp);
        }

        Ok(Self::build_command(&interpretations))
    }

    fn get_token_type(token: &str) -> Option<TokenType> {
        match token {
            "site" | "atcoder" => Some(TokenType::Site),
            "language" | "rust" => Some(TokenType::Language),
            "contest" => Some(TokenType::ContestId),
            "problem" => Some(TokenType::ProblemId),
            _ => None,
        }
    }

    fn interpret_token(&self, token: &str) -> Result<TokenInterpretation> {
        let mut interpretations = Vec::new();

        // エテゴリ直接マッチを試みる
        if let Some(token_type) = Self::get_token_type(token) {
            interpretations.push((token_type, token.to_string()));
            return Ok(TokenInterpretation {
                token: token.to_string(),
                interpretations,
            });
        }

        // エイリアス解決を試みる
        if let Some((category, original)) = self.config.resolve_alias(token) {
            if let Some(token_type) = Self::get_token_type(&category) {
                interpretations.push((token_type, original));
                return Ok(TokenInterpretation {
                    token: token.to_string(),
                    interpretations,
                });
            }
        }

        // 解釈できなかった場合は空の解釈リストを返す
        Ok(TokenInterpretation {
            token: token.to_string(),
            interpretations,
        })
    }

    fn assign_interpreted_tokens(
        interpretations: &[TokenInterpretation],
    ) -> (Option<String>, Option<String>, Option<String>, Option<String>) {
        let mut site = None;
        let mut language = None;
        let mut contest_id = None;
        let mut problem_id = None;

        for interp in interpretations {
            for (token_type, value) in &interp.interpretations {
                match token_type {
                    TokenType::Site => site = Some(value.clone()),
                    TokenType::Language => language = Some(value.clone()),
                    TokenType::ContestId => contest_id = Some(value.clone()),
                    TokenType::ProblemId => problem_id = Some(value.clone()),
                }
            }
        }

        (site, language, contest_id, problem_id)
    }

    fn assign_uninterpreted_tokens(
        interpretations: &[TokenInterpretation],
        contest_id: Option<String>,
        problem_id: Option<String>,
    ) -> (Option<String>, Option<String>) {
        let mut contest_id = contest_id;
        let mut problem_id = problem_id;
        
        // エイリアスとして解釈できなかったトークンを収集
        let mut tokens = interpretations
            .iter()
            .filter(|i| i.interpretations.is_empty());

        // contest_idが未設定の場合、最初の未解釈トークンをcontest_idとして使用
        if contest_id.is_none() {
            if let Some(token) = tokens.next() {
                contest_id = Some(token.token.clone());
            }
        }

        // problem_idが未設定で、まだ未解釈トークンが残っている場合
        // 次の未解釈トークンをproblem_idとして使用
        if problem_id.is_none() {
            if let Some(token) = tokens.next() {
                problem_id = Some(token.token.clone());
            }
        }

        (contest_id, problem_id)
    }

    fn build_command(interpretations: &[TokenInterpretation]) -> CommandContext {
        let (site, language, contest_id, problem_id) = Self::assign_interpreted_tokens(interpretations);
        let (contest_id, problem_id) = Self::assign_uninterpreted_tokens(
            interpretations,
            contest_id,
            problem_id,
        );

        let command = Command::Open {
            site,
            contest_id,
            problem_id,
            language,
        };

        CommandContext::new(command)
    }
} 