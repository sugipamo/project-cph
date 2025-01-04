use cph::config::Config;

#[tokio::main]
async fn main() -> cph::error::Result<()> {
    // 設定を読み込む
    let config = Config::load()?;

    // コマンドライン引数を取得
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        println!("使用方法: cph <command> [args...]");
        return Ok(());
    }

    // コマンドを実行
    // TODO: 実際のコマンド実行処理を実装

    Ok(())
}
