use anyhow::Result;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Problem {
    pub id: Uuid,
    pub name: String,
    pub url: Option<String>,
    pub platform: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestCase {
    pub id: Uuid,
    pub problem_id: Uuid,
    pub input: String,
    pub expected_output: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Submission {
    pub id: Uuid,
    pub problem_id: Uuid,
    pub code: String,
    pub language: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
}

#[async_trait::async_trait]
pub trait Repository<T>: Send + Sync {
    async fn create(&self, entity: &T) -> Result<T>;
    async fn find_by_id(&self, id: Uuid) -> Result<Option<T>>;
    async fn find_all(&self) -> Result<Vec<T>>;
    async fn update(&self, entity: &T) -> Result<T>;
    async fn delete(&self, id: Uuid) -> Result<()>;
}

#[async_trait::async_trait]
pub trait ProblemRepository: Repository<Problem> {
    async fn find_by_name(&self, name: &str) -> Result<Option<Problem>>;
    async fn find_by_platform(&self, platform: &str) -> Result<Vec<Problem>>;
}

#[async_trait::async_trait]
pub trait TestCaseRepository: Repository<TestCase> {
    async fn find_by_problem_id(&self, problem_id: Uuid) -> Result<Vec<TestCase>>;
}

#[async_trait::async_trait]
pub trait SubmissionRepository: Repository<Submission> {
    async fn find_by_problem_id(&self, problem_id: Uuid) -> Result<Vec<Submission>>;
    async fn find_latest_by_problem_id(&self, problem_id: Uuid) -> Result<Option<Submission>>;
}