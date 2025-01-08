use anyhow::{Result, anyhow};
use crate::contest::model::{Command, CommandContext};
use crate::message::{contest, common};
use petgraph::graph::NodeIndex;
use petgraph::Direction;

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

    /// コマンド文字列をパースします。
    /// 
    /// # Errors
    /// 
    /// 以下の場合にエラーを返します：
    /// - 入力が空の場合
    /// - トークンの解釈に失敗した場合
    pub fn parse(&self, input: &str) -> Result<CommandContext> {
        let tokens: Vec<&str> = input.split_whitespace().collect();
        if tokens.is_empty() {
            return Err(anyhow!(common::error("invalid_input", "入力が空です")));
        }

        let mut interpretations = Vec::new();
        for token in tokens {
            let token_interp = self.interpret_token(token)?;
            interpretations.push(token_interp);
        }

        Ok(Self::build_command(&interpretations))
    }

    fn get_token_type(parent: &str) -> Option<TokenType> {
        match parent {
            "site" => Some(TokenType::Site),
            "language" => Some(TokenType::Language),
            "contest" => Some(TokenType::ContestId),
            "problem" => Some(TokenType::ProblemId),
            _ => None,
        }
    }

    fn get_parent_nodes(
        graph: &petgraph::Graph<String, ()>,
        node_idx: NodeIndex,
    ) -> Vec<String> {
        graph
            .neighbors_directed(node_idx, Direction::Incoming)
            .filter_map(|parent| graph.node_weight(parent).cloned())
            .collect()
    }

    fn interpret_token(&self, token: &str) -> Result<TokenInterpretation> {
        let mut interpretations = Vec::new();
        let (graph, node_indices) = self.config.build_alias_graph();
        
        if let Some(&node_idx) = node_indices.get(token) {
            let parents = Self::get_parent_nodes(&graph, node_idx);
            let token_types: Vec<_> = parents
                .iter()
                .filter_map(|parent| Self::get_token_type(parent))
                .collect();

            if token_types.len() > 1 {
                return Err(anyhow!(contest::error(
                    "parse_error",
                    format!("トークン '{token}' は複数の方法で解釈できます")
                )));
            }

            if let Some(token_type) = token_types.first() {
                interpretations.push((token_type.clone(), token.to_string()));
                return Ok(TokenInterpretation {
                    token: token.to_string(),
                    interpretations,
                });
            }
        }

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

        // 未解釈トークンがある場合、優先度に基づいて解釈
        // contest (priority: 2) > problem (priority: 1)
        
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