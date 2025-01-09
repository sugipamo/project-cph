use std::time::Duration;
use tokio::time::sleep;
use tokio::sync::oneshot;
use anyhow::{Result, anyhow};

/// タイムアウト制御を行う構造体
///
/// # Fields
/// * `duration` - タイムアウトまでの時間
/// * `cancel_tx` - タイムアウト時のキャンセル用送信機
#[derive(Debug)]
pub struct TimeoutController {
    duration: Duration,
    cancel_tx: Option<oneshot::Sender<()>>,
}

impl TimeoutController {
    /// 新しいTimeoutControllerインスタンスを作成します
    ///
    /// # Arguments
    /// * `duration` - タイムアウトまでの時間
    ///
    /// # Returns
    /// * `Self` - 新しいTimeoutControllerインスタンス
    #[must_use = "この関数は新しいTimeoutControllerインスタンスを返します"]
    pub const fn new(duration: Duration) -> Self {
        Self {
            duration,
            cancel_tx: None,
        }
    }

    /// タイムアウト監視を開始します
    ///
    /// # Returns
    /// * `Result<oneshot::Receiver<()>>` - タイムアウト通知用の受信機
    ///
    /// # Errors
    /// * 監視が既に開始されている場合
    pub fn start(&mut self) -> Result<oneshot::Receiver<()>> {
        if self.cancel_tx.is_some() {
            return Err(anyhow!("タイムアウト監視は既に開始されています"));
        }

        let (tx, rx) = oneshot::channel();
        self.cancel_tx = Some(tx);
        Ok(rx)
    }

    /// タイムアウト監視を停止します
    pub fn stop(&mut self) {
        if let Some(tx) = self.cancel_tx.take() {
            let _ = tx.send(());
        }
    }

    /// 指定された処理をタイムアウト付きで実行します
    ///
    /// # Arguments
    /// * `future` - 実行する非同期処理
    ///
    /// # Returns
    /// * `Result<T>` - 処理の結果
    ///
    /// # Errors
    /// * タイムアウトが発生した場合
    /// * 処理がエラーを返した場合
    pub async fn run<T, F>(&mut self, future: F) -> Result<T>
    where
        F: std::future::Future<Output = Result<T>>,
    {
        let mut rx = self.start()?;

        tokio::select! {
            result = future => {
                self.stop();
                result
            }
            _ = sleep(self.duration) => {
                self.stop();
                Err(anyhow!("処理がタイムアウトしました"))
            }
            _ = &mut rx => {
                Err(anyhow!("処理がキャンセルされました"))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_timeout_success() {
        let mut controller = TimeoutController::new(Duration::from_secs(1));
        let result = controller.run(async {
            sleep(Duration::from_millis(100)).await;
            Ok(42)
        }).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 42);
    }

    #[tokio::test]
    async fn test_timeout_failure() {
        let mut controller = TimeoutController::new(Duration::from_millis(100));
        let result = controller.run(async {
            sleep(Duration::from_secs(1)).await;
            Ok(42)
        }).await;
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("タイムアウト"));
    }

    #[tokio::test]
    async fn test_timeout_cancel() {
        let mut controller = TimeoutController::new(Duration::from_secs(1));
        let rx = controller.start().unwrap();
        controller.stop();
        assert!(rx.await.is_ok());
    }
} 