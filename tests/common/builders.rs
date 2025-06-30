use std::path::PathBuf;

#[derive(Default)]
pub struct TestScenarioBuilder {
    problem: Option<String>,
    test_cases: Vec<(String, String)>,
    solution_file: Option<PathBuf>,
    expected_results: Vec<bool>,
}

impl TestScenarioBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn given_problem(mut self, problem: impl Into<String>) -> Self {
        self.problem = Some(problem.into());
        self
    }

    pub fn with_test_case(mut self, input: impl Into<String>, expected_output: impl Into<String>) -> Self {
        self.test_cases.push((input.into(), expected_output.into()));
        self
    }

    pub fn when_submit(mut self, solution: impl Into<PathBuf>) -> Self {
        self.solution_file = Some(solution.into());
        self
    }

    pub fn expect_all_pass(mut self) -> Self {
        self.expected_results = vec![true; self.test_cases.len()];
        self
    }

    #[allow(dead_code)]
    pub fn expect_results(mut self, results: Vec<bool>) -> Self {
        self.expected_results = results;
        self
    }

    pub fn build(self) -> TestScenario {
        TestScenario {
            problem: self.problem.expect("Problem name is required"),
            test_cases: self.test_cases,
            solution_file: self.solution_file.expect("Solution file is required"),
            expected_results: self.expected_results,
        }
    }
}

#[allow(dead_code)]
pub struct TestScenario {
    pub problem: String,
    pub test_cases: Vec<(String, String)>,
    pub solution_file: PathBuf,
    pub expected_results: Vec<bool>,
}

#[derive(Default)]
pub struct ConfigBuilder {
    app_name: Option<String>,
    docker_enabled: bool,
    test_timeout: Option<u64>,
    language: Option<String>,
}

impl ConfigBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_app_name(mut self, name: impl Into<String>) -> Self {
        self.app_name = Some(name.into());
        self
    }

    pub fn with_docker_enabled(mut self, enabled: bool) -> Self {
        self.docker_enabled = enabled;
        self
    }

    pub fn with_test_timeout(mut self, timeout: u64) -> Self {
        self.test_timeout = Some(timeout);
        self
    }

    pub fn with_language(mut self, language: impl Into<String>) -> Self {
        self.language = Some(language.into());
        self
    }

    pub fn build(self) -> String {
        format!(
            r#"[app]
name = "{}"
version = "0.1.0"

[docker]
enabled = {}

[test]
timeout = {}
language = "{}"
"#,
            self.app_name.unwrap_or_else(|| "test-app".to_string()),
            self.docker_enabled,
            self.test_timeout.unwrap_or(30),
            self.language.unwrap_or_else(|| "cpp".to_string())
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scenario_builder() {
        let scenario = TestScenarioBuilder::new()
            .given_problem("two-sum")
            .with_test_case("1 2\n", "3\n")
            .with_test_case("5 7\n", "12\n")
            .when_submit("solution.cpp")
            .expect_all_pass()
            .build();

        assert_eq!(scenario.problem, "two-sum");
        assert_eq!(scenario.test_cases.len(), 2);
        assert_eq!(scenario.expected_results, vec![true, true]);
    }

    #[test]
    fn test_config_builder() {
        let config = ConfigBuilder::new()
            .with_app_name("my-app")
            .with_docker_enabled(true)
            .with_test_timeout(60)
            .with_language("rust")
            .build();

        assert!(config.contains("name = \"my-app\""));
        assert!(config.contains("enabled = true"));
        assert!(config.contains("timeout = 60"));
        assert!(config.contains("language = \"rust\""));
    }
}