pub mod state;

#[derive(Debug, Clone)]
pub struct Contest {
    pub id: String,
    pub name: String,
    pub url: String,
    pub site: String,
    pub contest_id: String,
    pub problem_id: String,
    pub language: String,
}

impl Contest {
    pub fn new(site: String, contest_id: String, problem_id: String, language: String, url: String) -> Self {
        Self {
            id: format!("{}_{}", site, problem_id),
            name: format!("{} - {}", contest_id, problem_id),
            url,
            site,
            contest_id,
            problem_id,
            language,
        }
    }
}

#[derive(Debug, Clone)]
pub struct TestCase {
    pub input: String,
    pub expected: String,
    pub path: String,
}

impl TestCase {
    pub fn new(input: String, expected: String) -> Self {
        Self {
            input,
            expected,
            path: String::new(),
        }
    }
} 