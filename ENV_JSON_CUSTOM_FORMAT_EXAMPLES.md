# env.json カスタムフォーマット使用例

## 🎯 **追加されたコマンド**

### **Python環境**

| コマンド | エイリアス | 説明 |
|----------|------------|------|
| `./cph.sh test` | `t` | 従来のデフォルトテスト |
| `./cph.sh test_format` | `tf` | カスタムフォーマットテスト |
| `./cph.sh test_compact` | `tc` | コンパクト表示テスト |
| `./cph.sh test_detailed` | `td` | 詳細表示テスト |

### **C++環境**

| コマンド | エイリアス | 説明 |
|----------|------------|------|
| `./cph.sh test` | `t` | 従来のデフォルトテスト |
| `./cph.sh test_format` | `tf` | カスタムフォーマットテスト（C++） |
| `./cph.sh test_performance` | `tp` | パフォーマンス重視テスト |

## 🎨 **出力例**

### **1. デフォルト（変更なし）**
```bash
./cph.sh python test
```
```
Testing sample-1.in
✓ PASS
Testing sample-2.in
✗ FAIL
Expected:
2
Got:
1
```

### **2. カスタムフォーマット**
```bash
./cph.sh python test_format
# または
./cph.sh python tf
```
```
sample-1.in................... │ ✅   PASS     │       0.023s
sample-2.in................... │ ❌   FAIL     │       0.041s
    Expected: 2
    Got:      1
sample-long-name.in........... │ 💥  ERROR     │       0.002s
    Error: ValueError: invalid input
Results: 001/003 tests passed (33.3%)
```

### **3. コンパクト表示**
```bash
./cph.sh python test_compact
# または
./cph.sh python tc
```
```
[✅]        sample-1.in ( 23ms)
[❌]        sample-2.in ( 41ms) Expected: 2, Got: 1
[💥] sample-long-name.in (  2ms) Error: ValueError: invalid input
✨ 1/3 tests passed (33.3%)
```

### **4. 詳細表示**
```bash
./cph.sh python test_detailed
# または
./cph.sh python td
```
```
Test: sample-1.in.................... | Status: ✅  PASS  | Time:    0.023s | Memory:    23ms
Test: sample-2.in.................... | Status: ❌  FAIL  | Time:    0.041s | Memory:    41ms
  ✓ Expected: 2
  ✗ Actual:   1
  📊 Diff:     See above
Test: sample-long-name.in............ | Status: 💥 ERROR  | Time:    0.002s | Memory:     2ms
  💥 Error:    ValueError: invalid input
  📍 Details:  Program execution failed
📋 Test Summary: 001 passed / 002 failed / 003 total ( 33.33% success rate)
```

### **5. C++ パフォーマンステスト**
```bash
./cph.sh cpp test_performance
# または
./cph.sh cpp tp
```
```
⚡ sample-1.in............ │ ✅  PASS   │    15ms
⚡ sample-2.in............ │ ❌  FAIL   │    28ms
   Expected: 2
   Got:      1
⚡ sample-3.in............ │ 💥 ERROR   │     3ms
   Error: Compilation failed
⚡ Performance Test: 1/3 passed (33.3%) | Avg: 15ms
```

## 🔧 **設定の詳細**

### **Python format構文の機能**

```python
# 基本的な置換
"{test_name} | {status}"
# → "sample-1 | PASS"

# 幅指定とパディング
"{test_name:.<30}"          # 左寄せ、ドットで30文字まで埋める
"{status:^10}"              # 中央寄せ、10文字幅
"{time_formatted:>12}"      # 右寄せ、12文字幅

# 数値フォーマット
"{execution_time:>8.3f}s"   # 右寄せ、8文字幅、小数点以下3桁
"{time_ms:>5d}ms"           # 右寄せ、5文字幅、整数
"{passed:03d}"              # 3桁ゼロパディング

# パーセント表示
"{pass_rate:.1f}%"          # 小数点以下1桁のパーセント
"{pass_rate:>6.2f}%"        # 右寄せ、6文字幅、小数点以下2桁
```

### **利用可能な変数**

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `test_name` | テストファイル名 | `sample-1.in` |
| `status` | 実行結果 | `PASS`, `FAIL`, `ERROR` |
| `status_symbol` | ステータス記号 | `✅`, `❌`, `💥` |
| `expected_output` | 期待される出力 | `2` |
| `actual_output` | 実際の出力 | `1` |
| `error_message` | エラーメッセージ | `ValueError: invalid input` |
| `execution_time` | 実行時間（秒） | `0.023` |
| `time_ms` | 実行時間（ミリ秒） | `23` |
| `time_formatted` | フォーマット済み時間 | `0.023s` |
| `passed` | 成功テスト数 | `1` |
| `total` | 総テスト数 | `3` |
| `failed` | 失敗テスト数 | `2` |
| `pass_rate` | 成功率 | `33.3` |

### **フォーマット指定子の例**

```python
# 文字列フォーマット
"{test_name:<20}"           # 左寄せ、20文字
"{test_name:>20}"           # 右寄せ、20文字  
"{test_name:^20}"           # 中央寄せ、20文字
"{test_name:.<20}"          # 左寄せ、ドットで埋める
"{test_name:*^20}"          # 中央寄せ、アスタリスクで埋める

# 数値フォーマット
"{time_ms:d}"               # 整数
"{time_ms:5d}"              # 5文字幅の整数
"{time_ms:05d}"             # 5文字幅、ゼロパディング
"{execution_time:.3f}"      # 小数点以下3桁
"{execution_time:8.3f}"     # 8文字幅、小数点以下3桁
"{pass_rate:.1%}"           # パーセント表示（自動的に100倍）
```

## 📋 **カスタム設定の作成**

### **独自フォーマットの追加**

既存のenv.jsonを編集して、独自のテストコマンドを追加できます：

```json
{
  "python": {
    "commands": {
      "my_custom_test": {
        "aliases": ["mct"],
        "description": "私のカスタムテスト",
        "steps": [{
          "type": "test",
          "allow_failure": true,
          "show_output": true,
          "cmd": ["python3", "{workspace_path}/{source_file_name}"],
          "output_format": "template",
          "format_options": {
            "template_syntax": "python",
            "strict_formatting": true,
            "templates": {
              "default": "🎯 {test_name} → {status_symbol}",
              "pass": "🎯 {test_name} → {status_symbol} ({time_ms}ms)",
              "fail": "🎯 {test_name} → {status_symbol} Expected: '{expected_output}' Got: '{actual_output}'",
              "error": "🎯 {test_name} → {status_symbol} {error_message}",
              "summary": "🏆 Final Score: {passed}/{total} ({pass_rate:.0f}%)"
            }
          }
        }]
      }
    }
  }
}
```

### **shared/env.jsonのプリセット活用**

共通設定から既定のフォーマットを選択：

```json
{
  "format_options": {
    "template_syntax": "python",
    "strict_formatting": true,
    "preset": "competitive"
  }
}
```

## 🚀 **使用のコツ**

### **1. 段階的な移行**
- まず `./cph.sh python tf` で基本的なカスタムフォーマットを試す
- 気に入ったら `test_detailed` や `test_compact` も試す
- 独自フォーマットは少しずつカスタマイズ

### **2. 言語別の最適化**
- **Python**: デバッグ情報重視 (`test_detailed`)
- **C++**: パフォーマンス重視 (`test_performance`) 
- **共通**: 見やすさ重視 (`test_format`)

### **3. 出力の調整**
- ターミナル幅に応じてテンプレートの文字数を調整
- 重要な情報（時間、成功率）を右寄せで見やすく
- エラー情報は詳細に、成功情報は簡潔に

### **4. チーム開発での活用**
- プロジェクト固有のテンプレートを作成
- 成功率やパフォーマンス指標を統一
- CI/CDでの使用を考慮したフォーマット

---

## 🎉 **カスタムフォーマット機能を活用して、より効率的な競技プログラミング開発を！**