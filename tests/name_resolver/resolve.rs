use cph::contest::parse::NameResolver;

#[test]
fn test_resolve_exact_match() {
    let mut resolver = NameResolver::new("command".to_string());
    resolver.register_alias("test", "test");
    
    assert_eq!(resolver.resolve("test"), Some("test".to_string()));
}

#[test]
fn test_resolve_alias() {
    let mut resolver = NameResolver::new("command".to_string());
    resolver.register_alias("test", "t");
    
    assert_eq!(resolver.resolve("t"), Some("test".to_string()));
}

#[test]
fn test_resolve_unknown() {
    let resolver = NameResolver::new("command".to_string());
    assert_eq!(resolver.resolve("unknown"), None);
}

#[test]
fn test_resolve_case_sensitive() {
    let mut resolver = NameResolver::new("site".to_string());
    resolver.register_alias("atcoder", "ac");
    
    assert_eq!(resolver.resolve("ac"), Some("atcoder".to_string()));
    assert_eq!(resolver.resolve("AC"), None);
}

#[test]
fn test_resolve_multiple_aliases() {
    let mut resolver = NameResolver::new("site".to_string());
    resolver.register_alias("atcoder", "ac");
    resolver.register_alias("atcoder", "at");
    
    assert_eq!(resolver.resolve("ac"), Some("atcoder".to_string()));
    assert_eq!(resolver.resolve("at"), Some("atcoder".to_string()));
} 