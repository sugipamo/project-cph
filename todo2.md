# docker/config.rsのハードコード解消

## 1. 現状の問題点
- `Languages`構造体が固定的
- 言語設定がハードコード
- 拡張性が低い

## 2. 修正手順
1. **構造体の変更**
```rust
// 変更前
pub struct Languages {
    pub python: LanguageConfig,
    pub rust: LanguageConfig,
}

// 変更後
pub struct Languages {
    pub languages: HashMap<String, LanguageConfig>,
}
```

2. **runner.yamlの更新**
```yaml
languages:
  python:
    image: "python:3.9-slim"
    compile: null
    run: ["python", "-u", "-c"]
  rust:
    image: "rust:latest"
    compile: ["rustc", "main.rs"]
    run: ["./main"]
  cpp:
    image: "gcc:latest"
    compile: ["g++", "-std=c++17", "-O2", "main.cpp"]
    run: ["./a.out"]
```

3. **実装の更新**
- `RunnerConfig`の読み込み処理の更新
- `get_language_config`の簡素化
- エラーハンドリングの改善

## 3. 影響範囲
1. **直接的な影響**
   - `test`コマンド
   - `submit`コマンド
   - Docker関連の処理全般

2. **間接的な影響**
   - 言語設定の検証
   - テンプレート生成
   - エラーメッセージ

## 4. 実装順序
1. 構造体の更新
2. YAMLファイルの更新
3. 読み込み処理の実装
4. 依存箇所の更新

## 5. 検証項目
- 既存の言語が正常に動作するか
- 新しい言語の追加が可能か
- エラー処理が適切か
- パフォーマンスへの影響 