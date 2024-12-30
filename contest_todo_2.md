# 実装計画詳細

## フェーズ1: テンプレート構造の変更
予想所要時間: 2-3時間

1. contest_template/の再構成
   - [x] 各言語ディレクトリの作成（pypy, rust, cpp）
   - [ ] 各言語用の基本ファイル作成
     - solution.[ext]
     - generator.[ext]
     - .moveignore
   - [ ] 既存のテンプレートファイルを新構造に移動

2. 設定ファイルの更新
   - [ ] src/config/languages.yamlの更新
     ```yaml
     # 更新例
     rust:
       template_path: "contest_template/rust"
       moveignore_path: "contest_template/rust/.moveignore"
     ```

## フェーズ2: active_contest構造の変更
予想所要時間: 3-4時間

1. ディレクトリ構造の変更
   - [ ] 問題ごとのディレクトリ作成スクリプト実装
   - [ ] test/ディレクトリの自動作成機能追加
   - [ ] .moveignoreの自動配置機能実装

2. ファイル移行スクリプト作成
   ```rust
   // 実装すべき主な機能
   - 問題IDの抽出
   - ディレクトリ作成
   - ファイル移動
   - テストケース移動
   ```

## フェーズ3: コードベースの更新
予想所要時間: 4-5時間

1. src/contest/mod.rs
   - [ ] get_source_pathの更新
     ```rust
     // 新しいパス形式
     format!("active_contest/{}/solution.{}", problem_id, extension)
     ```

2. src/cli/commands/の更新
   - [ ] open.rs
     - テストケースダウンロードパスの更新
     - 問題ディレクトリ作成ロジックの追加
   - [ ] generate.rs
     - 新ディレクトリ構造対応
   - [ ] work.rs
     - ファイル移動処理の更新

3. src/oj/mod.rs
   - [ ] openメソッドの更新
     - テストケース保存先の変更
     - ディレクトリ構造確認処理の追加

## フェーズ4: テストとドキュメント
予想所要時間: 2-3時間

1. テスト更新
   - [ ] helpers/mod.rsの更新
   - [ ] 新構造用統合テストの追加
   - [ ] 既存テストの修正

2. ドキュメント更新
   - [ ] configuration.md
   - [ ] usage.md

## 移行手順

1. 開発ブランチの作成
   ```bash
   git checkout -b feature/directory-structure-update
   ```

2. フェーズごとの実装とテスト
   - 各フェーズ完了後にテストを実行
   - PRレビュー
   - マージ

3. 最終確認
   - [ ] すべてのテストが通ることを確認
   - [ ] 手動での動作確認
   - [ ] ドキュメントの最終確認

予想総所要時間: 11-15時間 