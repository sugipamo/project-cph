# src_check配下の動的インポート整理要件

## 現状分析

### プロジェクト構造
- `src_check/main.py` - エントリーポイント（シンプル版）
- `src_check/src_processors/` - 大量の処理モジュール群
  - `auto_correct/` - 自動修正系（argument_processors, file_organizers, import_dependency_reorganizer等）
  - `rules/` - チェックルール群（16個のチェッカー）
  - `broken_imports_checker.py` - 現在のメイン処理
- `src_check/models/` - データモデル
- `src_check/tools/` - ツール群
- `src_check/transformers/` - 変換処理

### 現在の実行方式
- `cwd=./project-cph`から`python3 src_check/main.py`を実行
- ファイルを辞書順で降順にしてDFSでmain.py探索
- 各ファイルは`cwd=./project-cph`で実行される
- 現在は`broken_imports_checker.py`のみを実行（シンプル版）

### 確認した問題
- 122件の壊れたインポート
- 2件の循環インポート
- src_check配下が大量のモジュールで「ごちゃごちゃ」状態

## 要件

### 1. 動的インポート導入による整理
- ファイルを辞書順で降順にソート
- DFS（深度優先探索）でmain.py探索実装
- 各モジュールの動的インポートを実現
- `cwd=./project-cph`での実行環境維持

### 2. 整理対象ディレクトリ
- `src_check/src_processors/auto_correct/` - 自動修正系
- `src_check/src_processors/rules/` - チェックルール系
- その他のsrc_processors配下モジュール

### 3. 技術要件
- 動的インポート（`importlib`使用）による処理選択
- DFS探索アルゴリズムの実装
- 現在の実行環境（cwd）の維持
- エラーハンドリング強化

### 4. 制約事項
- CLAUDE.mdの制約に従う：
  - デフォルト値使用禁止
  - フォールバック処理禁止
  - 品質管理コードはsrc_check/配下維持
- 現在のCLI実行形式を維持
- 既存の処理結果（CheckResult）形式維持

## 実装方針

### Phase 1: 動的インポート基盤
1. `src_check/dynamic_importer.py` - 動的インポート管理
2. `src_check/module_explorer.py` - DFS探索実装
3. `src_check/main.py` - エントリーポイント更新

### Phase 2: モジュール整理
1. 各処理モジュールの統一インターフェース化
2. 実行順序の制御
3. エラーハンドリング統一

### Phase 3: 検証
1. 既存機能の動作確認
2. パフォーマンス検証
3. エラーケースの確認

## 期待効果
- src_check配下の構造化と整理
- 処理の選択的実行
- 保守性向上
- 拡張性向上