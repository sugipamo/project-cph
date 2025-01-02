# コマンドパターン再構築 作業報告

## 変更点の概要

1. コマンドパターンの統合
- 各コマンドで重複していたパターンを共通の`ordered`と`unordered`セクションに集約
- `commands`セクションをエイリアス定義のみに簡略化

2. 言語指定機能の拡張
- `test`と`submit`コマンドに言語指定オプションを追加
- 例：`test abc001 a rust`, `submit abc001 a python`

3. `test submit`コマンドの検討
- テスト実行後に提出を行う連続実行コマンドとしての可能性
- エラーハンドリングの方針：前のコマンドが失敗した場合、後続のコマンドは実行しない

## 新しい設計方針

1. メソッド呼び出し順の制御
- `config.yaml`の`commands`セクションで実行順を定義
- 設定と実装の分離による保守性の向上

2. 環境情報の優先順位
- `language`, `contest_id`, `problem`は作業環境の情報として最優先
- これらの実行順序は相互に独立

3. コマンドパターンの簡略化
- フラットな構造での管理
- パターンの重複排除
- エイリアスは`config.yaml`で一元管理

## 次のステップ

1. 実装の優先順位
- 環境情報の更新処理
- エラーハンドリングの実装
- `test submit`連続実行の実装

2. 検証が必要な項目
- 環境情報更新の順序独立性
- 言語指定の動作確認
- エラー発生時の挙動

3. 将来の拡張性
- 新しいコマンドの追加（例：`scrape`）
- コマンド固有のパターン管理
- エラーメッセージの改善

## 技術的な詳細

### コマンドパターンの例
```yaml
ordered:
  - ["site_id", "command", "problem_id"]
  - ["command", "problem_id"]
  - ["site_id", "command", "problem_id", "language"]
  - ["command", "problem_id", "language"]
  ...

unordered:
  - ["site_id", "contest_id", "command", "problem_id"]
  - ["contest_id", "command", "problem_id"]
  ...

commands:
  test:
    aliases: ["test", "t", "check"]
  submit:
    aliases: ["submit", "s", "sub"]
  ...
```

### 想定される使用例
1. 基本的なコマンド
   - `test abc001 a`
   - `submit abc001 a`

2. 言語指定付きコマンド
   - `test abc001 a rust`
   - `submit abc001 a python`

3. サイト指定付きコマンド
   - `ac test abc001 a`
   - `ac submit abc001 a python`

## 注意点
- 既存のテストケースの更新が必要
- 環境情報の更新処理の実装が必要
- エラーハンドリングの詳細な設計が必要 