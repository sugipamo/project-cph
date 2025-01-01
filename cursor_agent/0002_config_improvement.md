# 設定ファイル改善検討報告書

## 現状の課題

### 1. 設定の重複
- `system.source_file`と`languages._base.template.pattern`で同様の設定が重複
- ファイル名パターンの一元管理が必要

### 2. Online Judge Tool連携
- 現在は`site_ids`を静的に設定
- 将来的にはOnline Judge Toolから動的に取得したい
- 移行期間中は現在の静的設定を維持

### 3. テンプレート設定の改善
- テンプレートディレクトリ名が静的
- 言語名を動的に使用したい
- パスの柔軟な設定が必要

## 改善案

### 1. 設定の一元化
```yaml
system:
  templates:
    patterns:
      solution: "${CPH_SOLUTION_FILE-solution.{extension}}"
      generator: "${CPH_GENERATOR_FILE-generator.{extension}}"
      tester: "${CPH_TESTER_FILE-tester.{extension}}"
    directory: "${CPH_TEMPLATE_DIR-{name}}"
```

### 2. Online Judge Tool連携
```yaml
languages:
  rust:
    site_ids:
      _source: "online_judge_tool"  # 将来的な設定
      _fallback:  # フォールバック設定
        atcoder: "5054"
```

### 3. 動的テンプレート設定
```yaml
languages:
  rust:
    template:
      directory: "${CPH_LANG_TEMPLATE_DIR-{name}}"  # {name}は言語名に置換
```

## 実装の優先度

### 優先度：高
1. 設定の一元化
   - 重複排除による保守性向上
   - 設定変更の影響範囲縮小

### 優先度：中
1. 動的テンプレート設定
   - テンプレート管理の柔軟性向上
   - 既存機能への影響は限定的

### 優先度：低
1. Online Judge Tool連携
   - 現状の静的設定で問題なし
   - 将来的な拡張性のための準備

## 次のステップ

1. 設定の一元化
   - `system.templates`セクションの作成
   - 既存の重複設定の移行
   - 参照先の更新

2. テンプレート設定の改善
   - 動的パス生成の実装
   - テンプレートディレクトリ構造の整理

3. Online Judge Tool連携の準備
   - インターフェースの設計
   - フォールバック機能の実装 