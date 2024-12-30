use crate::{
    error::Result,
    contest::Contest,
};
use std::path::PathBuf;

pub fn run_test(problem_id: &str, active_contest_dir: PathBuf) -> Result<()> {
    let contest = Contest::new(active_contest_dir)?;
    let test_dir = contest.root.join("test").join(problem_id);

    if !test_dir.exists() {
        return Err("テストディレクトリが見つかりません。問題を開いてテストケースをダウンロードしてください。".into());
    }

    // テストの実行
    Ok(())
}

#[cfg(test)]
mod tests {
    // テストの実装
} 