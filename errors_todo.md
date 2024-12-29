# エラー状況と対策

## 1. 構造体のフィールド名の不一致と不要な実装

### LanguageConfig構造体
現在の定義:
```rust
pub struct LanguageConfig {
    pub image: String,
    pub compile: Option<String>,
    pub run: String,
}
```

エラーのある参照:
- `image_name` -> `image`
- `run_cmd` -> `run`
- `compile_cmd` -> `compile`
- `workspace_dir` (動的生成に変更)
- `file_extension` (不要なため削除)

影響を受けるファイル:
- src/docker/runner/container.rs
- src/docker/runner/compiler.rs

### RunnerConfig構造体
現在の定義:
```rust
pub struct RunnerConfig {
    pub languages: Languages,
    pub timeout_seconds: u64,
    pub memory_limit_mb: i64,
}
```

エラーのある参照:
- `memory_limit_mb` (追加)
- `timeout_seconds` (追加)

影響を受けるファイル:
- src/docker/runner/container.rs
- src/docker/runner/io.rs
- src/docker/runners/mod.rs

## 2. 警告
- src/docker/config.rs: 未使用のインポート `PathBuf`
- src/docker/runner/container.rs: 未使用のインポート `futures::StreamExt`

## 対策手順

1. LanguageConfig構造体の簡素化
   ```rust
   pub struct LanguageConfig {
       pub image: String,
       pub compile: Option<String>,
       pub run: String,
   }
   ```
   - workspace_dirは言語名から動的生成する関数を追加
   - file_extensionフィールドは削除

2. RunnerConfig構造体の修正
   ```rust
   pub struct RunnerConfig {
       pub languages: Languages,
       pub timeout_seconds: u64,
       pub memory_limit_mb: i64,
   }
   ```

3. 設定ファイル（runner.yaml）の更新
   ```yaml
   timeout_seconds: 5
   memory_limit_mb: 128
   languages:
     python:
       image: "python:3.9-slim"
       compile: null
       run: ["python", "-u", "-c"]
     # 他の言語も同様に更新
   ```

4. 各ファイルの修正
   - src/docker/runner/container.rs
     - フィールド名の更新
     - workspace_dirの動的生成を使用
   - src/docker/runner/compiler.rs
     - フィールド名の更新
     - workspace_dirの動的生成を使用
   - src/docker/runner/io.rs
     - timeout_secondsの参照を更新
   - src/docker/runners/mod.rs
     - timeout_secondsの参照を更新

5. 警告の解消
   - 未使用のインポートを削除

## 実装の優先順位

1. 構造体の定義修正（LanguageConfig, RunnerConfig）
2. 設定ファイルの更新
3. 各ファイルでのフィールド参照の更新
4. テストコードの更新
5. 警告の解消

## 注意点

- 構造体の変更に伴い、シリアライズ/デシリアライズの処理も影響を受ける
- テストケースの期待値も更新が必要
- 後方互換性は新しい構造に完全移行する 