# src_check ツール集

このディレクトリにはsrc_checkで使用される補助ツールが含まれています。

## インポート修正ツール

### import_fixer.py
**高機能なインポート自動修正ツール**

依存関係ベースのファイル再配置後のインポートエラーを自動修正します。

#### 機能
- 基本的な移動パターンの自動修正
- 複雑なケースの警告表示
- 詳細なレポート生成
- 信頼度スコアによる修正品質の評価

#### 使用方法
```bash
# 基本実行
python3 src_check/tools/import_fixer.py

# ドライランモード（変更をプレビュー）
python3 src_check/tools/import_fixer.py --dry-run
```

#### 出力
- `import_fix_report_final.md` - 詳細なレポート
- 自動修正されたファイル
- 手動確認が必要な警告一覧

### quick_import_fixer.py
**シンプルなクイック修正ツール**

最も一般的なインポートパターンを迅速に修正します。

#### 使用方法
```bash
python3 src_check/tools/quick_import_fixer.py
```

#### 修正パターン
- CLI関連: `src.cli` → `src.core.cli_app`
- Workflow関連: `src.workflow.*` → `src.core.workflow.*`
- Configuration関連: `src.configuration.*` → `src.core.configuration.*`
- その他の一般的な移動パターン

## 使い分け

### import_fixer.py を使用する場合
- 大規模な再配置後の包括的な修正
- 詳細な分析レポートが必要
- 手動確認が必要なケースを特定したい

### quick_import_fixer.py を使用する場合
- 迅速な修正が必要
- 基本的なパターンのみを対象
- シンプルな出力で十分

## 注意事項

1. **バックアップ**: 修正前に必ずGitでコミットしてください
2. **構文チェック**: 修正後は `python3 -m compileall src/` で構文確認
3. **テスト実行**: 修正後は関連テストを実行してください
4. **段階的実行**: 大きな変更は段階的に実行することを推奨

## 開発者向け

これらのツールは依存関係ベースフォルダ構造整理ツールと連携して動作します。

- メインツール: `src_check/src_processors/auto_correct/import_dependency_reorganizer/`
- 設定ファイル: `reorganizer_config.json`
- 実行ログ: `logs/reorganizer_*.json`