# Config構造体への設定機能移行

## 現状
- `Contest`構造体に`get_config`メソッドが実装されており、設定値の取得に使用されている
- `Config`構造体に設定値の取得機能が実装済み
- 現在のエラーは`get_config`メソッドが`Contest`構造体に存在しないことによるもの

## 作業計画
1. `Contest`構造体内の`config`フィールドを使用して設定値を取得するように修正
2. 以下のファイルを修正：
   - src/oj/mod.rs
   - src/cli/commands/open.rs
   - src/cli/commands/submit.rs

## 実装方針
- `self.contest.get_config()`の呼び出しを`self.contest.config.get()`に変更
- エラー処理は`Config`構造体の`ConfigError`を`String`に変換して処理

## 影響範囲
- 設定値の取得に関する処理のみ
- 既存の機能に影響を与えない
- 型安全性は`Config`構造体の実装により保証される

## 作業難易度
- 低：単純な置換作業が主
- エラー処理の変更は最小限 