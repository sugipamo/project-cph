# 設定ファイルのマージ機能実装TODO

## 1. 設定ファイルの優先順位
- `active_contest/*.yaml` > `src/config/*.yaml`
- 対象ファイル: `docker.yaml`, `languages.yaml`, `oj.yaml`, `sites.yaml`

## 2. 構造体の修正
- 各設定構造体に`Default`トレイトを実装
  ```rust
  #[derive(Debug, Serialize, Deserialize, Default)]
  pub struct OJConfig {
      #[serde(default)]  // フィールドがない場合はデフォルト値を使用
      pub submit: SubmitConfig,
      #[serde(default)]
      pub test: TestConfig,
  }
  ```

## 3. マージ機能の実装
1. `src/config/merge.rs`を作成
   ```rust
   pub trait ConfigMerge {
       fn merge(&mut self, other: Self);
   }
   ```

2. 各設定構造体に`ConfigMerge`トレイトを実装
   - 再帰的にフィールドをマージ
   - `Option`型を使用して、値の有無を判定

## 4. 設定読み込み機能の修正
1. `ConfigPaths`の拡張
   ```rust
   pub struct ConfigPaths {
       base_dir: PathBuf,      // src/config
       active_dir: PathBuf,    // active_contest
       // ... 既存のフィールド
   }
   ```

2. 設定読み込みロジックの実装
   ```rust
   fn load_config<T: Default + ConfigMerge>() -> Result<T> {
       // 1. ベース設定を読み込み
       // 2. アクティブコンテスト設定があれば読み込み
       // 3. マージして返す
   }
   ```

## 5. エラーハンドリング
- ベース設定ファイルが存在しない場合はエラー
- アクティブコンテスト設定ファイルが存在しない場合は無視
- パース失敗時は適切なエラーメッセージを表示

## 6. テストの追加
1. ユニットテスト
   - マージ機能のテスト
   - 各設定構造体のデフォルト値テスト
   - 設定読み込みのテスト

2. 結合テスト
   - 実際のファイルを使用したテスト
   - 優先順位の確認
   - 部分的な設定の上書きテスト

## 7. ドキュメント
- `docs/configuration.md`の更新
  - 設定ファイルの優先順位の説明
  - マージ動作の説明
  - 設定例の追加 