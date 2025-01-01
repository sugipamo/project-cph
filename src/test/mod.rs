use crate::{
    error::Result,
    contest::Contest,
    config::Config,
};

pub fn run_test(problem_id: &str) -> Result<()> {
    // 設定を取得
    let config = Config::load()
        .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

    // コンテストを読み込む
    let contest = Contest::new(&config, problem_id)?;

    // テストディレクトリを取得
    let test_dir = contest.active_contest_dir.join("test").join(problem_id);

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