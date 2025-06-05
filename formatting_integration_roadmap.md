# フォーマット関数統合ロードマップ

## 段階的統合実行計画

### Phase 1: 基盤構築 ✅ (完了)

#### 成果物
- `src/pure_functions/formatting/core/` - 基底レイヤー
  - `string_formatter.py` - 基本フォーマット機能
  - `template_processor.py` - テンプレート処理
  - `validation.py` - バリデーション機能

- `src/pure_functions/formatting/specialized/` - 特化レイヤー
  - `execution_formatter.py` - ExecutionContext特化
  - `output_formatter.py` - 出力フォーマット特化  
  - `path_formatter.py` - パス関連特化

- `src/pure_functions/formatting/__init__.py` - 統合API

#### 機能比較

| 機能 | 従来 | 新統合版 | 改善点 |
|-----|------|--------|--------|
| 基本フォーマット | format_utils.py | core/string_formatter.py | API統一、パフォーマンス向上 |
| 実行コンテキスト | execution_context_formatter_pure.py | specialized/execution_formatter.py | 基底レイヤー活用、拡張性向上 |
| 出力フォーマット | output_manager_formatter_pure.py | specialized/output_formatter.py | 柔軟性向上、カスタマイズ対応 |

### Phase 2: 互換性テスト

#### 2.1 既存テストの実行確認

```bash
# 既存のフォーマット関連テストが全て通ることを確認
pytest tests/context/utils/test_format_utils.py -v
pytest tests/pure_functions/test_execution_context_formatter_pure.py -v  
pytest tests/pure_functions/test_output_manager_formatter_pure.py -v
```

#### 2.2 新APIのテスト作成

```bash
# 新しいフォーマット機能のテストファイル作成
tests/pure_functions/formatting/
├── test_core_string_formatter.py
├── test_specialized_execution_formatter.py
├── test_specialized_output_formatter.py
└── test_unified_api.py
```

#### 2.3 性能ベンチマーク

```python
# パフォーマンステストの実装例
def test_performance_comparison():
    # 従来版 vs 新統合版の処理速度比較
    # メモリ使用量の比較
    # キャッシュ効率の確認
```

### Phase 3: 段階的移行

#### 3.1 新規コードでの新API使用

```python
# 推奨される新しいインポート方法
from src.pure_functions.formatting import (
    UnifiedFormatter,
    ExecutionContextFormatter, 
    OutputFormatter
)

# または個別機能のインポート
from src.pure_functions.formatting import (
    format_with_context,
    ExecutionFormatData,
    create_execution_format_dict
)
```

#### 3.2 既存コードの段階的移行

**優先度1: 新規機能・修正時に移行**
```python
# Before (従来)
from src.context.utils.format_utils import format_with_missing_keys

# After (新統合版)
from src.pure_functions.formatting import format_with_missing_keys
```

**優先度2: 既存機能の強化**
```python
# 従来の単純な関数呼び出し
formatted, missing = format_with_missing_keys(template, **context)

# 新統合版のクラスベースAPI（オプション）
formatter = UnifiedFormatter(default_context)
formatted = formatter.format_string(template, additional_context)
```

#### 3.3 段階的警告の実装

```python
# 旧ファイルでの非推奨警告追加
import warnings

def format_with_missing_keys(*args, **kwargs):
    warnings.warn(
        "format_utils.format_with_missing_keys is deprecated. "
        "Use src.pure_functions.formatting.format_with_missing_keys instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    from src.pure_functions.formatting import format_with_missing_keys as new_func
    return new_func(*args, **kwargs)
```

### Phase 4: 完全移行

#### 4.1 旧ファイルの置き換え

```bash
# 段階的にファイルを置き換え
src/context/utils/format_utils.py → 非推奨化
src/pure_functions/execution_context_formatter_pure.py → 移行完了
src/pure_functions/output_manager_formatter_pure.py → 移行完了
```

#### 4.2 インポートパスの更新

```python
# 全体的なインポートパス統一
# 従来の分散したインポート
from src.context.utils.format_utils import format_with_missing_keys
from src.pure_functions.execution_context_formatter_pure import create_format_dict
from src.pure_functions.output_manager_formatter_pure import extract_output_data

# 統合後の一元化されたインポート
from src.pure_functions.formatting import (
    format_with_missing_keys,
    create_execution_format_dict as create_format_dict,  # 互換性エイリアス
    extract_output_data
)
```

### Phase 5: クリーンアップ

#### 5.1 旧ファイルの削除

```bash
# 完全移行後に削除予定
rm src/context/utils/format_utils.py
rm src/pure_functions/execution_context_formatter_pure.py
rm src/pure_functions/output_manager_formatter_pure.py
```

#### 5.2 テストの統合

```bash
# 古いテストファイルの内容を新しいテストに統合
tests/context/utils/test_format_utils.py → tests/pure_functions/formatting/
tests/pure_functions/test_execution_context_formatter_pure.py → 統合
tests/pure_functions/test_output_manager_formatter_pure.py → 統合
```

#### 5.3 ドキュメント更新

```markdown
# API更新ドキュメントの作成
- 移行ガイド
- 新API使用例
- パフォーマンス改善点
- 今後の開発方針
```

## 実装優先順位と期間予測

### 即座に実行可能 (当日)
- [x] 基盤ディレクトリ構造の作成
- [x] 基底レイヤーの実装
- [x] 特化レイヤーの実装  
- [x] 統合APIの実装

### 短期 (1-2日)
- [ ] 既存テストの実行確認
- [ ] 新APIのテスト作成
- [ ] 性能ベンチマークテスト
- [ ] 互換性確認

### 中期 (1週間)
- [ ] 段階的移行の開始
- [ ] 新規コードでの新API使用
- [ ] 非推奨警告の実装
- [ ] 一部既存コードの移行

### 長期 (2-4週間)
- [ ] 全既存コードの移行
- [ ] 旧ファイルの削除
- [ ] テストの統合・整理
- [ ] ドキュメント更新

## リスク管理

### 技術的リスク
1. **パフォーマンス劣化**
   - 対策: 詳細なベンチマークテスト
   - 監視: CI/CDでの性能監視

2. **API破綻**
   - 対策: 包括的な互換性テスト
   - 回避: エイリアス提供による段階的移行

3. **複雑性増加**
   - 対策: 明確な責務分離とドキュメント化
   - 監視: コード品質メトリクス

### 運用リスク
1. **開発効率の一時的低下**
   - 対策: 十分な移行期間の確保
   - 支援: 移行ガイドとサンプルコード

2. **バグの混入**
   - 対策: 段階的移行と十分なテスト
   - 検出: 自動テストとコードレビュー

## 成功指標

### 定量的指標
- [ ] 既存テスト: 100% パス
- [ ] 性能: 現在と同等以上 (±5%以内)
- [ ] コード重複: 30%以上削減
- [ ] テストカバレッジ: 95%以上維持

### 定性的指標
- [ ] 開発者体験の向上
- [ ] コードの可読性向上
- [ ] メンテナンス性の向上
- [ ] API一貫性の確保

## 次のステップ

1. **Phase 2の開始**: 既存テストの実行確認
2. **性能テストの実装**: ベンチマーク環境の構築
3. **移行戦略の詳細化**: 具体的なファイル単位での移行計画
4. **チーム内共有**: 統合計画の周知と合意形成