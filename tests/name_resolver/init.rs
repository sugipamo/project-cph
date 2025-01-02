use cph::contest::parse::NameResolver;

#[test]
fn test_new_resolver() {
    let resolver = NameResolver::new("test_type".to_string());
    assert_eq!(resolver.get_param_type(), "test_type");
    assert!(resolver.is_empty());
}

#[test]
fn test_register_alias() {
    let mut resolver = NameResolver::new("command".to_string());
    resolver.register_alias("test", "t");
    
    assert_eq!(resolver.get_aliases_len(), 1);
    assert_eq!(resolver.get_alias("t"), Some("test".to_string()));
}

#[test]
fn test_multiple_aliases() {
    let mut resolver = NameResolver::new("site".to_string());
    resolver.register_alias("atcoder", "ac");
    resolver.register_alias("atcoder", "at");
    
    assert_eq!(resolver.get_aliases_len(), 2);
    assert_eq!(resolver.get_alias("ac"), Some("atcoder".to_string()));
    assert_eq!(resolver.get_alias("at"), Some("atcoder".to_string()));
}

#[test]
fn test_overwrite_alias() {
    let mut resolver = NameResolver::new("command".to_string());
    resolver.register_alias("test", "t");
    resolver.register_alias("submit", "t");
    
    assert_eq!(resolver.get_aliases_len(), 1);
    assert_eq!(resolver.get_alias("t"), Some("submit".to_string()));
} 