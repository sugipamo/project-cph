#[cfg(test)]
mod tests {
    use super::*;
    use serde_yaml::Value;

    fn create_test_config() -> Config {
        let value = serde_yaml::from_str(r#"
            system:
                source_file:
                    solution: "main.rs"
                docker:
                    timeout_seconds: 2
                    memory_limit_mb: 256.0
                submit:
                    auto_yes: true
            languages:
                rust:
                    aliases: ["rs"]
                    extension: "rs"
        "#).unwrap();
        Config::new(value)
    }

    #[test]
    fn test_basic_config_access() {
        let config = create_test_config();
        
        // 元の記法での設定値の取得
        let solution: String = config.get("system.source_file.solution").unwrap();
        assert_eq!(solution, "main.rs");

        let timeout: i64 = config.get("system.docker.timeout_seconds").unwrap();
        assert_eq!(timeout, 2);

        let auto_yes: bool = config.get("system.submit.auto_yes").unwrap();
        assert!(auto_yes);

        // ConfigNodeを介した設定値の取得
        let solution = config.get_node("system.source_file.solution")
            .and_then(|node| node.as_typed::<String>())
            .unwrap();
        assert_eq!(solution, "main.rs");
    }

    #[test]
    fn test_config_validation() {
        let config = create_test_config();
        
        // カスタムスキーマの作成
        struct TimeoutSchema;
        impl CustomSchema for TimeoutSchema {
            fn validate(&self, value: &Value) -> ConfigResult<()> {
                if let Value::Number(n) = value {
                    if let Some(timeout) = n.as_i64() {
                        if timeout > 0 && timeout <= 10 {
                            return Ok(());
                        }
                    }
                }
                Err(ConfigError::ValidationError {
                    message: "タイムアウトは1から10秒の間である必要があります".to_string(),
                })
            }

            fn describe(&self) -> String {
                "タイムアウト値の検証".to_string()
            }
        }

        // 有効な値でのテスト
        let node = config.get("system.docker.timeout_seconds").unwrap();
        let schema = ConfigSchema::Custom(Arc::new(TimeoutSchema));
        assert!(node.with_value(Value::Number(2.into())).is_ok());

        // 無効な値でのテスト
        assert!(node.with_value(Value::Number(11.into())).is_err());
    }

    #[test]
    fn test_config_change_notification() {
        use std::sync::atomic::{AtomicBool, Ordering};
        use std::sync::Arc;

        struct TestListener {
            called: Arc<AtomicBool>,
        }

        impl ConfigListener for TestListener {
            fn on_change(&self, _old: &ConfigNode, _new: &ConfigNode) {
                self.called.store(true, Ordering::SeqCst);
            }
        }

        let called = Arc::new(AtomicBool::new(false));
        let config = create_test_config()
            .with_listener(TestListener { called: called.clone() });

        // 設定値の変更
        if let Ok(node) = config.get("system.docker.timeout_seconds") {
            let _new_node = node.with_value(Value::Number(3.into())).unwrap();
            assert!(called.load(Ordering::SeqCst));
        }
    }

    #[test]
    fn test_type_conversion() {
        let config = create_test_config();

        // 文字列への変換テスト
        let node = config.get("system.docker.timeout_seconds").unwrap();
        let str_val: String = node.as_typed().unwrap();
        assert_eq!(str_val, "2");

        // 真偽値への変換テスト
        let node = config.get("system.submit.auto_yes").unwrap();
        let bool_val: bool = node.as_typed().unwrap();
        assert!(bool_val);

        // 数値への変換テスト
        let node = config.get("system.docker.timeout_seconds").unwrap();
        let num_val: i64 = node.as_typed().unwrap();
        assert_eq!(num_val, 2);
    }
} 