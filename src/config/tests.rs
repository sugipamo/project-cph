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
        
        // 基本的な設定値の取得
        let solution: String = config.get("system.source_file.solution").unwrap();
        assert_eq!(solution, "main.rs");

        let timeout: i64 = config.get("system.docker.timeout_seconds").unwrap();
        assert_eq!(timeout, 2);

        let auto_yes: bool = config.get("system.submit.auto_yes").unwrap();
        assert!(auto_yes);

        // ConfigNodeを介した設定値の取得
        let solution_node = config.get_node("system.source_file.solution").unwrap();
        let solution: String = solution_node.as_typed().unwrap();
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
                    message: "Timeout must be between 1 and 10 seconds".to_string(),
                })
            }

            fn describe(&self) -> String {
                "Timeout value validation".to_string()
            }
        }

        // スキーマを持つ新しいノードの作成
        let node = ConfigNode::new(Value::Number(2.into()), "timeout".to_string())
            .with_schema(ConfigSchema::Custom(Arc::new(TimeoutSchema)));

        // スキーマによる検証
        assert!(ConfigSchema::Custom(Arc::new(TimeoutSchema))
            .validate(&Value::Number(2.into()))
            .is_ok());
        assert!(ConfigSchema::Custom(Arc::new(TimeoutSchema))
            .validate(&Value::Number(11.into()))
            .is_err());
    }

    #[test]
    fn test_type_conversion() {
        let config = create_test_config();

        // 文字列型への変換
        let solution: String = config.get("system.source_file.solution").unwrap();
        assert_eq!(solution, "main.rs");

        // 数値型への変換
        let timeout: i64 = config.get("system.docker.timeout_seconds").unwrap();
        assert_eq!(timeout, 2);

        // 真偽値への変換
        let auto_yes: bool = config.get("system.submit.auto_yes").unwrap();
        assert!(auto_yes);

        // 型変換エラーのテスト
        let result: ConfigResult<bool> = config.get("system.source_file.solution");
        assert!(result.is_err());
    }

    #[test]
    fn test_path_resolution() {
        let config = create_test_config();

        // 存在するパスの解決
        assert!(config.exists("system.docker.timeout_seconds"));
        assert!(config.exists("languages.rust.aliases"));

        // 存在しないパスの解決
        assert!(!config.exists("nonexistent.path"));
        assert!(!config.exists("system.invalid"));
    }

    #[test]
    fn test_metadata() {
        // メタデータを持つノードの作成
        let node = ConfigNode::new(Value::String("test".to_string()), "test".to_string())
            .with_description("Test configuration value".to_string())
            .with_schema(ConfigSchema::Primitive(PrimitiveType::String));

        // メタデータの検証
        assert!(node.metadata.description.is_some());
        assert!(node.metadata.schema.is_some());
    }

    #[test]
    fn test_pattern_matching() {
        let config = create_test_config();

        // system.docker.*のパターンマッチング
        let docker_settings = config.get_all("system\\.docker\\..*").unwrap();
        assert_eq!(docker_settings.len(), 2); // timeout_seconds と memory_limit_mb

        // 存在しないパターンのマッチング
        let empty_result = config.get_all("nonexistent\\..*").unwrap();
        assert!(empty_result.is_empty());
    }
} 