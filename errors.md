# プロジェクトのリンターエラー

## 1. `workspace`モジュールから`contest`モジュールへの移行（✅完了）

### 完了した修正

以下の3つのファイルで`Contest`構造体への移行を完了：

1. `src/cli/commands/open.rs`:
- ✅ インポート文を更新
- ✅ `Workspace`を`Contest`に変更
- ✅ `workspace.contest_id`を`contest.contest_id`に変更
- ✅ `workspace.get_source_path`を`contest.get_source_path`に変更

2. `src/cli/commands/generate.rs`:
- ✅ インポート文を更新
- ✅ `Workspace`を`Contest`に変更
- ✅ `workspace.language.extension()`を`contest.language.to_string()`に変更
- ✅ `workspace.get_source_path`を`contest.get_source_path`に変更

3. `src/test/mod.rs`:
- ✅ インポート文を更新
- ✅ `Workspace`を`Contest`に変更
- ✅ `workspace.root`を`contest.root`に変更

### 確認結果
- コンパイルテスト：✅成功
- `workspace`関連のエラー：✅解消

## 2. 新たに発見された警告

### 未使用のフィールド
1. `src/cli/commands/test.rs`:
   - `context: CommandContext`フィールドが未使用

### 未使用の変数（`src/bin/cph.rs`）
1. `Commands::Work`:
   - 未使用の`contest_id`
2. `Commands::Test`:
   - 未使用の`problem_id`
3. `Commands::Language`:
   - 未使用の`language`
4. `Commands::Open`:
   - 未使用の`problem_id`
5. `Commands::Submit`:
   - 未使用の`problem_id`
6. `Commands::Generate`:
   - 未使用の`problem_id`

### 対応方針
1. 未使用フィールドの対応：
   - `test.rs`の`context`フィールドの使用方法を確認
   - 必要に応じてフィールドを削除または使用を実装

2. 未使用変数の対応：
   - 各コマンドの実装を確認
   - 変数を使用する処理を実装
   - または、不要な場合は`_`でパターンマッチをスキップ 