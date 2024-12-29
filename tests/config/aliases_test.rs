#[cfg(test)]
use cph::config::aliases::AliasConfig;

#[test]
fn test_resolve_language() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // Python
    assert_eq!(config.resolve_language("python"), Some("python".to_string()));
    assert_eq!(config.resolve_language("Python"), Some("python".to_string()));
    assert_eq!(config.resolve_language("python3"), Some("python".to_string()));
    
    // PyPy
    assert_eq!(config.resolve_language("pypy"), Some("pypy".to_string()));
    assert_eq!(config.resolve_language("PyPy"), Some("pypy".to_string()));
    assert_eq!(config.resolve_language("pypy3"), Some("pypy".to_string()));
    assert_eq!(config.resolve_language("py"), Some("pypy".to_string()));
    
    // 存在しない言語
    assert_eq!(config.resolve_language("invalid"), None);
}

#[test]
fn test_resolve_command() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // test command
    assert_eq!(config.resolve_command("test"), Some("test".to_string()));
    assert_eq!(config.resolve_command("t"), Some("test".to_string()));
    assert_eq!(config.resolve_command("check"), Some("test".to_string()));
    
    // language command
    assert_eq!(config.resolve_command("language"), Some("language".to_string()));
    assert_eq!(config.resolve_command("l"), Some("language".to_string()));
    assert_eq!(config.resolve_command("lang"), Some("language".to_string()));
    
    // login command
    assert_eq!(config.resolve_command("login"), Some("login".to_string()));
    assert_eq!(config.resolve_command("auth"), Some("login".to_string()));
    
    // 存在しないコマンド
    assert_eq!(config.resolve_command("invalid"), None);
}

#[test]
fn test_resolve_site() {
    let config = AliasConfig::load("src/config/aliases.yaml").unwrap();
    
    // AtCoder
    assert_eq!(config.resolve_site("atcoder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("at-coder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("at_coder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("AtCoder"), Some("atcoder".to_string()));
    assert_eq!(config.resolve_site("ac"), Some("atcoder".to_string()));
    
    // 存在しないサイト
    assert_eq!(config.resolve_site("invalid"), None);
} 