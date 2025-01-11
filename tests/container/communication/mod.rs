use cphelper::container::communication::{Message, ControlMessage, StatusMessage};

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::sync::mpsc;

    #[tokio::test]
    async fn test_message_passing() {
        let (tx, mut rx) = mpsc::channel(32);
        
        // メッセージ送受信のテストを実装
    }

    #[tokio::test]
    async fn test_control_messages() {
        // 制御メッセージのテストを実装
    }

    #[tokio::test]
    async fn test_status_messages() {
        // ステータスメッセージのテストを実装
    }
} 