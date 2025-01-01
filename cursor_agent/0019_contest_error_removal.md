# Contest構造体のエラー処理と定数定義の簡素化

## 概要
- `ContestError`の削除
- 設定パスの定数定義の削除
- エラー処理の簡素化

## 変更理由
1. `ContestError`による細かいエラー分類は実際の使用上で利点が少ない
2. 設定パスの定数定義はかえってコードを複雑にしている
3. 基本的なエラーハンドリングで十分な場合が多い

## 具体的な変更
1. `ContestError`の削除：
   - `error.rs`ファイルの削除
   - `Result`型を`std::result::Result`に変更

2. 定数定義の削除：
   - 設定パスを直接文字列として使用
   - エラーメッセージを直接記述

3. エラー処理の簡素化：
```rust
// 変更前
self.config.get::<String>("system.contest_dir.active")
    .map_err(|e| ContestError::config(format!("アクティブディレクトリの設定取得に失敗: {}", e)))?;

// 変更後
self.config.get::<String>("system.contest_dir.active")
    .map_err(|e| format!("アクティブディレクトリの設定取得に失敗: {}", e))?;
```

## 期待される効果
1. コードの簡素化
2. エラーハンドリングの理解しやすさの向上
3. メンテナンス性の向上

## 影響範囲
- `src/contest/mod.rs`: エラー処理の変更
- `src/contest/error.rs`: ファイルの削除
- `src/error.rs`: `ContestError`関連コードの削除

## 作業難易度
低: 主に削除作業とシンプルな書き換え 