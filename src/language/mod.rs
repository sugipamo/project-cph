use std::path::PathBuf;
use crate::config::Config;
use crate::contest::error::{Result, ContestError};

/// ソリューションファイルのパスを取得
pub fn get_solution_path(config: &Config, problem_id: &str) -> Result<PathBuf> {
    let active_dir = config.get::<String>("languages.default.contest_dir.active")?;
    let solution_pattern = config.get::<String>("languages.default.templates.patterns.solution")?;
    let extension = config.get::<String>("languages.default.extension")?;
    
    let solution_file = solution_pattern.replace("{extension}", &extension);
    Ok(PathBuf::from(active_dir).join(problem_id).join(solution_file))
}

/// 言語設定を更新
pub fn update_language_setting(config: &Config, problem_id: &str, language: &str) -> Result<()> {
    // 言語が有効かチェック
    if !is_valid_language(config, language)? {
        return Err(ContestError::Validation {
            message: format!("無効な言語が指定されました: {}", language),
        });
    }

    let solution_path = get_solution_path(config, problem_id)?;
    if !solution_path.exists() {
        return Err(ContestError::FileSystem {
            message: "ソリューションファイルが存在しません".to_string(),
            source: std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "solution file not found"
            ),
            path: solution_path,
        });
    }

    // TODO: 実際の言語設定の更新処理を実装
    println!("言語を{}に設定しました", language);

    Ok(())
}

/// 言語が有効かチェック
fn is_valid_language(config: &Config, language: &str) -> Result<bool> {
    let languages: Vec<String> = config.get("languages")?;
    Ok(languages.contains(&language.to_string()))
}

/// 言語を設定
pub fn set_language(
    config: &Config,
    problem_id: &str,
    language: &str,
) -> Result<()> {
    update_language_setting(config, problem_id, language)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // TODO: テストを実装
} 