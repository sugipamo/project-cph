use wiremock::{
    matchers::{method, path},
    Mock, MockServer, ResponseTemplate,
};
use serde_json::json;

/// AtCoderのモックサーバー
pub struct AtCoderMock {
    server: MockServer,
}

impl AtCoderMock {
    /// モックサーバーを作成
    pub async fn start() -> Self {
        let server = MockServer::start().await;
        Self { server }
    }

    /// サーバーのURLを取得
    pub fn url(&self) -> String {
        self.server.uri()
    }

    /// ログイン状態をモック
    pub async fn mock_login(&self) {
        Mock::given(method("POST"))
            .and(path("/login"))
            .respond_with(ResponseTemplate::new(200))
            .mount(&self.server)
            .await;
    }

    /// 問題ページのアクセスをモック
    pub async fn mock_problem_page(&self, contest_id: &str, problem_id: &str) {
        let path = format!("/contests/{}/tasks/{}_{}", contest_id, contest_id, problem_id);
        Mock::given(method("GET"))
            .and(path(path))
            .respond_with(ResponseTemplate::new(200))
            .mount(&self.server)
            .await;
    }

    /// 提出APIをモック
    pub async fn mock_submit(&self, contest_id: &str, problem_id: &str) {
        let path = format!("/contests/{}/submit", contest_id);
        Mock::given(method("POST"))
            .and(path(path))
            .respond_with(ResponseTemplate::new(200).set_body_json(json!({
                "id": "submission_id",
                "problem_id": format!("{}_{}", contest_id, problem_id),
                "status": "AC"
            })))
            .mount(&self.server)
            .await;
    }

    /// エラーケースをモック
    pub async fn mock_error(&self, path: &str, status: u16, message: &str) {
        Mock::given(method("POST"))
            .and(path(path))
            .respond_with(
                ResponseTemplate::new(status)
                    .set_body_json(json!({ "error": message }))
            )
            .mount(&self.server)
            .await;
    }
} 