# テスト結果カスタムフォーマット実装ロードマップ

## 🎯 実装概要

**目標**: ./cph.sh testコマンドにPython format構文による結果フォーマット機能を追加
**期間**: 14-19時間（3-4週間）
**アプローチ**: 段階的実装による安全な機能追加

## 📋 実装ステップ

### Phase 1: 基盤構築 (6-8時間)

#### 1.1 抽象化レイヤー実装 (2-3時間)
**ファイル**: `src/operations/formatters/base_format_engine.py`

```python
# 実装内容
- FormatSyntaxType(Enum): PYTHON, PRINTF, JINJA2, TEMPLATE
- FormatContext(dataclass): 不変フォーマットコンテキスト
- FormatResult(class): 成功/失敗情報付き結果
- FormatEngine(ABC): 抽象基底クラス
```

**実装詳細**:
- `FormatEngine.supports_syntax()`: 構文サポート検証
- `FormatEngine.format()`: フォーマット実行
- 型安全性確保（frozen dataclass活用）

#### 1.2 Python Formatエンジン (3-4時間)
**ファイル**: `src/operations/formatters/python_format_engine.py`

```python
# 実装内容
- PythonFormatEngine: 基本Python format構文
- EnhancedPythonFormatEngine: 拡張機能付き
- 高度なformat仕様対応: {name:format_spec}, {name!conversion}
```

**機能詳細**:
- 既存`format_utils.py`との統合
- 高度なformat仕様の自動検出
- エラーハンドリングとフォールバック

#### 1.3 フォーマットマネージャー (1-2時間)
**ファイル**: `src/operations/formatters/format_manager.py`

```python
# 実装内容
- FormatManager: エンジン統一管理
- エンジン自動検出機能
- グローバルインスタンス提供
```

### Phase 2: テスト結果統合 (5-7時間)

#### 2.1 テスト結果フォーマッタ拡張 (3-4時間)
**ファイル**: `src/operations/formatters/test_result_formatter.py`

```python
# 実装内容  
- AdvancedFormatOptions: 拡張フォーマットオプション
- TemplateBasedFormatter: テンプレートベースフォーマッタ
- デフォルトテンプレート定義
```

**統合ポイント**:
- 既存`TestResultFormatter`の拡張
- `unified_request_factory.py`での活用
- テストスクリプト生成との連携

#### 2.2 env.json設定処理 (2-3時間)
**場所**: `src/operations/factory/unified_request_factory.py` (ComplexRequestStrategy)

```python
# 追加実装
- format_optionsの解析処理
- テンプレート設定の適用
- 出力フォーマット選択ロジック
```

**設定例**:
```json
{
  "python": {
    "commands": {
      "test": {
        "steps": [{
          "type": "test",
          "output_format": "template",
          "format_options": {
            "template_syntax": "python",
            "templates": {
              "default": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}"
            }
          }
        }]
      }
    }
  }
}
```

### Phase 3: テストとドキュメント (3-4時間)

#### 3.1 包括的テスト作成 (2-3時間)
**ファイル**: 
- `tests/operations/formatters/test_base_format_engine.py`
- `tests/operations/formatters/test_python_format_engine.py`
- `tests/operations/formatters/test_format_manager.py`

**テストカバレッジ**:
- 基本フォーマット機能
- 高度なformat仕様
- エラーハンドリング
- パフォーマンステスト

#### 3.2 統合テスト (1時間)
**ファイル**: `tests/integration/test_custom_format_e2e.py`

**テストシナリオ**:
- env.json設定からの統合動作
- 複数フォーマット構文の切り替え
- エラー時のフォールバック

## 🔧 技術的実装詳細

### 統合ポイント1: unified_request_factory.py
**場所**: ComplexRequestStrategy.create_request() - TESTタイプ処理

**現在のコード**:
```python
# 219-248行: テストスクリプト生成
test_script = f'''
for i in {contest_current_path}/test/sample-*.in; do
    # ... テスト実行ロジック
done
'''
```

**拡張後**:
```python
# フォーマットオプション取得
format_options = step.get('format_options', {})
if format_options.get('output_format') == 'template':
    formatter = TemplateBasedFormatter()
    # テスト結果をカスタムフォーマットで出力
```

### 統合ポイント2: 既存format_utils.pyとの連携

**活用する既存機能**:
- `extract_format_keys()`: LRUキャッシュ付きキー抽出
- `format_with_missing_keys()`: 安全なフォーマット処理

**新機能との分担**:
- 既存: 基本的な{key}フォーマット
- 新規: 高度な{key:format_spec}フォーマット

## 📊 実装スケジュール

### Week 1: Phase 1 (6-8時間)
- **月**: 抽象化レイヤー (2-3h)
- **火**: Python Formatエンジン基本部分 (2h)
- **水**: Python Formatエンジン高度機能 (1-2h)
- **木**: フォーマットマネージャー (1-2h)

### Week 2: Phase 2 (5-7時間)
- **月**: テスト結果フォーマッタ設計 (2h)
- **火**: テンプレートベースフォーマッタ実装 (2h)
- **水**: env.json統合 (1-2h)
- **木**: unified_request_factory統合 (1h)

### Week 3: Phase 3 (3-4時間)
- **月**: 基本テスト作成 (2h)
- **火**: 統合テスト (1h)
- **水**: ドキュメント作成 (1h)

## 🧪 テスト戦略

### 単体テスト
```python
# test_python_format_engine.py
def test_basic_format():
    engine = PythonFormatEngine()
    context = FormatContext(data={"name": "sample-1", "status": "PASS"})
    result = engine.format("{name:.<20} | {status:^8}", context)
    assert result.formatted_text == "sample-1............ |   PASS  "

def test_advanced_format_spec():
    # {value:>10.3f}, {time:ms} 等の高度なformat仕様テスト
```

### 統合テスト
```python
# test_custom_format_e2e.py  
def test_env_json_custom_format():
    # env.jsonからのフォーマット設定読み込み
    # テスト実行とカスタムフォーマット出力確認
```

## 🎨 出力例

### デフォルトフォーマット
```
sample-1.in................... │ ✅   PASS    │       0.023s
sample-2.in................... │ ❌   FAIL    │       0.041s  
    Expected: 2
    Got:      1
```

### カスタムフォーマット例
```json
{
  "templates": {
    "default": "[{status_symbol}] {test_name:>25} ({time_ms:>4d}ms)",
    "summary": "Results: {passed:03d}/{total:03d} tests passed ({pass_rate:>6.2f}%)"
  }
}
```

```
[✅]              sample-1.in ( 23ms)
[❌]              sample-2.in ( 41ms)
[💥]    sample-long-name.in (  2ms)
Results: 001/003 tests passed ( 33.33%)
```

## 🔄 段階的移行戦略

### 1. 後方互換性確保
- 既存のテスト出力形式を完全保持
- `output_format`未指定時はデフォルト動作
- 新機能はオプトイン方式

### 2. 段階的機能公開
1. **基本Python format**: `{key}`, `{key:width}`
2. **高度なformat**: `{key:>10.3f}`, `{key!r}`  
3. **カスタムフォーマッタ**: 将来の`{time:ms}`等

### 3. 移行支援
- エラー時の詳細メッセージ
- 設定例のドキュメント提供
- デバッグモードでのフォーマット詳細表示

## ⚠️ リスク要因と対策

### リスク1: 既存コードへの影響
**対策**: 
- 完全な後方互換性維持
- オプトイン設計による影響最小化
- 包括的テストによる検証

### リスク2: パフォーマンス劣化
**対策**:
- LRUキャッシュの活用継続
- 軽量なformat仕様判定
- ベンチマークテスト実装

### リスク3: 複雑性の増大
**対策**:
- 責務分離された明確なアーキテクチャ
- 段階的実装による複雑性管理
- 十分なドキュメント化

## ✅ 成功指標

### 機能性
- [ ] Python format構文の完全サポート
- [ ] env.json設定の正常動作
- [ ] 既存テスト出力の完全互換

### 品質
- [ ] テストカバレッジ90%以上
- [ ] 全既存テストの通過維持
- [ ] パフォーマンス劣化なし

### 使いやすさ
- [ ] 直感的な設定方法
- [ ] 明確なエラーメッセージ
- [ ] 豊富な出力例とドキュメント

## 🚀 実装開始の準備状況

### ✅ 完了済み要素
- 包括的な設計ドキュメント
- 既存コード構造の理解
- テスト対象機能の特定
- 段階的実装計画

### 📋 実装開始時の初期タスク
1. `src/operations/formatters/`ディレクトリ作成
2. 基底クラス`base_format_engine.py`の実装開始
3. 既存`format_utils.py`との統合テスト
4. 最初のユニットテスト作成

---

**このロードマップにより、Python format構文に特化しつつ将来拡張可能な、安全で高品質なカスタムフォーマット機能の実装が可能になります。**