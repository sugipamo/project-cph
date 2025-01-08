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

    /// 新しいParserインスタンスを設定で初期化します
    #[must_use]
    pub const fn with_config(config: crate::contest::parse::config::Config) -> Self {
        Self { config }
    }

    /// `入力文字列`をパースして`CommandContext`を生成します
    /// 
    /// # Errors
    /// 
    /// - 入力文字列のパースに失敗した場合
    /// - コマンドの解釈に失敗した場合
    pub fn parse(&self, input: &str) -> Result<CommandContext> {
        let input = input.trim();
        if input.is_empty() {
            return Err(anyhow!("入力が空です"));
        }

        let tokens: Vec<&str> = input.split_whitespace().collect();
        Ok(self.parse_tokens(&tokens))
    }

    fn parse_tokens(&self, tokens: &[&str]) -> CommandContext {
        let mut interpretations = Vec::new();
        for token in tokens {
            let token_interp = self.interpret_token(token);
            interpretations.push(token_interp);
        }

        Self::build_command(&interpretations)
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

    /// トークンを解釈し、可能な解釈のリストを返します
    fn interpret_token(&self, token: &str) -> TokenInterpretation {
        let mut interpretations = Vec::new();

        // エイリアス解決を試みる
        if let Some((category, original)) = self.config.resolve_alias(token) {
            if let Some(token_type) = Self::get_token_type(&category) {
                interpretations.push((token_type, original));
                return TokenInterpretation {
                    token: token.to_string(),
                    interpretations,
                };
            }
        }

        // カテゴリ直接マッチを試みる
        if let Some(token_type) = Self::get_token_type(token) {
            interpretations.push((token_type, token.to_string()));
            return TokenInterpretation {
                token: token.to_string(),
                interpretations,
            };
        }

        // 解釈できなかった場合は空の解釈リストを返す
        TokenInterpretation {
            token: token.to_string(),
            interpretations,
        }
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
        let uninterpreted_tokens: Vec<_> = interpretations
            .iter()
            .filter(|i| i.interpretations.is_empty())
            .map(|i| i.token.clone())
            .collect();

        // 未解釈トークンがある場合、priorityの高い順に割り当てる
        if !uninterpreted_tokens.is_empty() {
            // priority=2のcontest_idを先に割り当て
            if contest_id.is_none() && !uninterpreted_tokens.is_empty() {
                contest_id = Some(uninterpreted_tokens[0].clone());
            }
            // priority=1のproblem_idを次に割り当て
            if problem_id.is_none() && uninterpreted_tokens.len() > 1 {
                problem_id = Some(uninterpreted_tokens[1].clone());
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