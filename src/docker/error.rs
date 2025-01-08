// このファイルは削除します。代わりにanyhow::Errorを直接使用します。
// エラーは以下のように作成します：
//
// ```rust
// use anyhow::{Error, Result, Context};
//
// // Dockerエラーの場合
// Err(anyhow!("Dockerエラー: {}", message))
//
// // 実行エラーの場合
// Err(anyhow!("実行エラー: {}", message))
//
// // コンパイルエラーの場合
// Err(anyhow!("コンパイルエラー: {}", message))
//
// // コンテナエラーの場合
// Err(anyhow!("コンテナエラー: {}", message))
//
// // 状態エラーの場合
// Err(anyhow!("状態エラー: {}", message))
// ``` 