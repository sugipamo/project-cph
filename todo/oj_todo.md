# OJ設定の実装TODO

## 1. 設定ファイルの作成
- `src/config/oj.yaml`を作成し、以下の設定項目を追加
  ```yaml
  submit:
    wait: 0  # デフォルトの待機時間
    auto_yes: true  # --yes フラグのデフォルト値
  
  test:
    directory: "test"  # テストケースを保存するディレクトリ名
  ```

## 2. 設定ファイルの読み込み機能の実装
- `src/config/mod.rs`に`OJConfig`構造体を追加
- YAML設定ファイルをパースする機能を実装
- デフォルト値の設定

## 3. `src/oj/mod.rs`の修正
- `OJContainer`に設定を読み込む機能を追加
- `submit`メソッドを設定に基づいて修正
- `open`メソッドのテストディレクトリパスを設定から取得するように修正

## 4. エラーハンドリング
- 設定ファイルが存在しない場合のデフォルト値の使用
- 不正な設定値のバリデーション

## 5. ドキュメント
- `docs/configuration.md`にOJ設定の項目を追加
- 設定例とオプションの説明を記載 