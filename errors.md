# プロジェクトのリンターエラー

## モジュール参照エラー

### 1. `workspace`モジュールから`contest`モジュールへの移行

#### 完了した修正

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

### 次のステップ
1. コンパイルテストの実行
2. 機能テストの実行
3. 以下の変更点の動作確認：
   - `language.extension()`から`language.to_string()`への変更の影響
   - ファイルパスの生成方法の一貫性
   - テンプレート生成の動作

### 注意点
- `Contest`構造体のメソッドが`Workspace`構造体と同じインターフェースを提供していることを確認
- 特に`language`関連のメソッド名の変更（`extension()`→`to_string()`）が適切か確認
- テストケースの更新が必要な可能性あり 