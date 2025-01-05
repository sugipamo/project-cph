use super::*;
use crate::config::Config;
use std::collections::HashMap;

#[test]
fn test_contest_creation() -> Result<()> {
    let mut config_map = HashMap::new();
    config_map.insert("system.contest_dir.active".to_string(), "/tmp/contest".to_string());
    config_map.insert("languages.default".to_string(), "rust".to_string());
    let config = Config::from_str(&serde_json::to_string(&config_map)?, Config::builder())?;

    let contest = Contest::new(config.clone(), "abc123")?;
    
    assert_eq!(contest.state().problem_id(), Some("abc123"));
    assert_eq!(contest.state().language(), Some("rust"));
    assert_eq!(contest.state().active_dir(), "/tmp/contest");
    Ok(())
}

#[test]
fn test_state_access() -> Result<()> {
    let config = Config::load()?;
    let mut contest = Contest::for_site_auth(config)?;
    
    contest.state_mut().set_problem("xyz987");
    assert_eq!(contest.state().problem_id(), Some("xyz987"));
    Ok(())
}

#[test]
fn test_config_and_fs_manager_access() -> Result<()> {
    let config = Config::load()?;
    let contest = Contest::for_site_auth(config.clone())?;
    
    assert!(std::ptr::eq(contest.config(), &config));
    assert!(contest.backup_manager().is_ok());
    Ok(())
}
