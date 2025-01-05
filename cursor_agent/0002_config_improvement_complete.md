# 設定ファイル改善作業報告書

## 完了した作業

### 1. テンプレート設定の一元化
- `system.source_file`を`system.templates`に移行
- ファイル名パターンを統一
- テンプレートディレクトリ設定を集約

### 2. Online Judge Tool連携の準備
- `site_ids`に`_source`と`_fallback`を追加
- 将来的な動的取得に対応する構造を整備
- 既存の設定値をフォールバック値として保持

### 3. 重複設定の削除
- 言語ごとの`template`設定を削除
- `system.templates`で一元管理
- 動的な値置換に対応

## 変更内容の詳細

### 1. システム設定の変更
```yaml
system:
  templates:
    patterns:
      solution: "${CPH_SOLUTION_FILE-solution.{extension}}"
      generator: "${CPH_GENERATOR_FILE-generator.{extension}}"
      tester: "${CPH_TESTER_FILE-tester.{extension}}"
    directory: "${CPH_TEMPLATE_DIR-{name}}"
```

### 2. 言語設定の変更
```yaml
languages:
  _base: &lang_base
    compile: []
    run: []
    aliases: []

  rust:
    site_ids:
      _source: "online_judge_tool"
      _fallback:
        atcoder: "5054"
```

## 改善された点

1. 設定の一貫性
   - テンプレート関連の設定が一箇所に集約
   - 命名規則の統一
   - 環境変数のデフォルト値を明確化

2. 拡張性の向上
   - Online Judge Tool連携の準備
   - 動的な設定値の生成に対応
   - フォールバック機構の導入

3. メンテナンス性の向上
   - 重複コードの削除
   - 設定の依存関係の明確化
   - コメントの整理

## 次のステップ

1. コード側の対応
   - 新しい設定構造への対応
   - テンプレート処理の更新
   - パス生成ロジックの修正

2. テストの更新
   - 新しい設定形式のテスト追加
   - テンプレート処理のテスト
   - エッジケースの確認

3. ドキュメントの更新
   - 新しい設定形式の説明
   - 環境変数の一覧更新
   - 移行ガイドの作成 