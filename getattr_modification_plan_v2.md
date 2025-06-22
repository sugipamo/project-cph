# getattr() デフォルト値修正計画書 v2.0

## 概要

CLAUDE.md準拠のため、プロジェクト内の `getattr()` デフォルト値使用を完全に削除する計画書です。
実際のコードベース調査に基づいた正確な修正対象と実装方針を示します。

## 修正対象の実態

### 現在の getattr() 使用状況（2024年調査結果）
ripgrep による全ファイル検索結果：**26箇所**

**分類別内訳：**
- 🔧 **修正対象**: 24箇所（CLAUDE.md違反）
- ✅ **修正不要**: 2箇所（適切な使用）

### 修正対象詳細（24箇所）

#### 1. Infrastructure Result Factory（13箇所）
**ファイル**: `src/infrastructure/result/result_factory.py`
**問題**: リクエストオブジェクトからの動的属性取得でデフォルト値使用

```python
# 修正対象コード例
result_path = path or getattr(request, "path", None)
result_op = op or getattr(request, "op", None)
result_cmd = cmd or getattr(request, "cmd", None)
operation_type = getattr(request, "operation_type", None)
```

**修正優先度**: 🔥 高（中核システム）

#### 2. Shell Driver（4箇所）
**ファイル**: `src/infrastructure/drivers/shell/shell_driver.py:35-38`
**問題**: リクエストからのオプション属性取得

```python
# 修正対象コード
cwd=getattr(request, 'cwd', None),
env=getattr(request, 'env', None),
inputdata=getattr(request, 'inputdata', None),
timeout=getattr(request, 'timeout', None)
```

**修正優先度**: 🔥 高（実行エンジン）

#### 3. Unified Driver（3箇所）
**ファイル**: `src/infrastructure/drivers/unified/unified_driver.py`
**問題**: リクエスト・レスポンスオブジェクトの動的属性アクセス

```python
# 修正対象コード例
request_type_name = getattr(request.request_type, 'name', str(request.request_type))
container_id=getattr(result, 'container_id', None),
image=getattr(result, 'image_id', None),
```

**修正優先度**: 🔥 高（統合ドライバー）

#### 4. Python Driver（2箇所）
**ファイル**: `src/infrastructure/drivers/python/python_driver.py:48,56`
**問題**: リクエストからのcwd属性取得

```python
# 修正対象コード
cwd=getattr(request, 'cwd', None)
```

**修正優先度**: 🟡 中（言語固有）

#### 5. Persistence Driver（2箇所）
**ファイル**: `src/infrastructure/drivers/persistence/persistence_driver.py:49,51`
**問題**: リクエストからのparams属性取得

```python
# 修正対象コード
getattr(request, 'params', ())
```

**修正優先度**: 🟡 中（データベース）

### 修正不要箇所（2箇所）

#### 1. Workflow Step Runner（2箇所）
**ファイル**: `src/workflow/step/step_runner.py:130,288`
**理由**: 動的属性アクセスが適切（テンプレートエンジン用途）

```python
# 適切な使用例
value = getattr(context, attr)  # デフォルト値なし
patterns = getattr(context, pattern_name)  # デフォルト値なし
```

## 修正方針

### 1. 統一的なアプローチ

**基本原則**: `hasattr()` + 直接アクセス + 設定システム活用

```python
# 修正前
value = getattr(obj, 'attr', None)

# 修正後
if hasattr(obj, 'attr'):
    value = obj.attr
else:
    value = config_manager.resolve_config(['defaults', 'attr'], type(obj.attr))
```

### 2. 設定ベースのデフォルト値管理

**原則**: すべてのデフォルト値は設定ファイルで管理

```python
# 新規設定ファイル作成
# config/system/infrastructure_defaults.json
{
  "infrastructure_defaults": {
    "shell": {
      "cwd": null,
      "env": {},
      "inputdata": null,
      "timeout": 30
    },
    "result": {
      "path": null,
      "op": null,
      "cmd": null,
      "operation_type": "unknown"
    }
  }
}
```

### 3. 型安全な属性アクセス

**プロトコル定義による型安全性確保**

```python
# protocols/request_protocols.py
from typing import Protocol, Optional

class ShellRequestProtocol(Protocol):
    cmd: str
    cwd: Optional[str]
    env: Optional[dict[str, str]]
    inputdata: Optional[str]
    timeout: Optional[int]

class ResultRequestProtocol(Protocol):
    path: Optional[str]
    op: Optional[str]
    cmd: Optional[str]
    operation_type: Optional[str]
```

## 実装計画

### Phase 1: 緊急対応（1-2日）

**対象**: Infrastructure Result Factory（13箇所）
**理由**: 最も影響範囲が大きい中核システム

1. **設定ファイル追加**
   ```bash
   # config/system/infrastructure_defaults.json 作成
   ```

2. **Result Factory修正**
   ```python
   # hasattr() + 設定システム活用
   if hasattr(request, 'path'):
       result_path = path or request.path
   else:
       result_path = path or self.config_manager.resolve_config(
           ['infrastructure_defaults', 'result', 'path'], str
       )
   ```

3. **テスト実行**
   ```bash
   # 修正後のテスト実行
   python -m pytest tests/infrastructure/result/ -v
   ```

### Phase 2: ドライバー層修正（2-3日）

**対象**: Shell, Unified, Python, Persistence Drivers（11箇所）

1. **ドライバー別設定追加**
2. **型安全な属性アクセス実装**
3. **互換性維持テスト**

### Phase 3: 品質保証（1日）

1. **getattr_checker.py 更新**
2. **CI/CD パイプライン修正**
3. **全体テスト実行**

## 技術的制約と対策

### 制約1: 動的属性の実行時決定
**問題**: リクエストタイプによって持つ属性が異なる
**対策**: プロトコル定義 + 型チェック

### 制約2: 後方互換性維持
**問題**: 既存のリクエストオブジェクトとの互換性
**対策**: 設定ファイルでのデフォルト値管理

### 制約3: パフォーマンス
**問題**: hasattr() + 設定システムアクセスのオーバーヘッド
**対策**: 設定キャッシュ活用（既存システム）

## リスク分析

### 高リスク領域
- **Result Factory**: 全操作に影響
- **Shell Driver**: 実行エンジンの中核

### 中リスク領域
- **Unified Driver**: ルーティング層
- **Python Driver**: 言語固有処理

### 低リスク領域
- **Persistence Driver**: データベース操作

## 成功指標

### 定量的指標
- ✅ getattr() デフォルト値使用: 0箇所
- ✅ 新規設定ファイル: 1個追加
- ✅ テスト通過率: 100%
- ✅ 品質チェック: PASS

### 定性的指標
- ✅ 型安全性の向上
- ✅ 設定管理の統一
- ✅ コードの可読性向上
- ✅ CLAUDE.md準拠

## 完了条件

1. **コード修正**: 24箇所の getattr() デフォルト値削除
2. **設定追加**: infrastructure_defaults.json 作成
3. **テスト**: 全テストケース PASS
4. **品質チェック**: getattr_checker.py PASS
5. **ドキュメント**: 修正内容の文書化

## 注意事項

### CLAUDE.md準拠事項
- ✅ デフォルト値の設定ファイル化
- ✅ 設定取得方法の統一
- ✅ 型安全性の確保
- ✅ 互換性維持コメントの追記

### 開発制約
- 🚫 設定ファイル編集は明示的許可必要
- 🚫 e2e.py 変更は明示的許可必要
- 🚫 フォールバック処理禁止

## 付録

### 修正対象ファイル一覧
1. `src/infrastructure/result/result_factory.py` - 13箇所
2. `src/infrastructure/drivers/shell/shell_driver.py` - 4箇所  
3. `src/infrastructure/drivers/unified/unified_driver.py` - 3箇所
4. `src/infrastructure/drivers/python/python_driver.py` - 2箇所
5. `src/infrastructure/drivers/persistence/persistence_driver.py` - 2箇所

### 設定ファイル構造
```
config/system/
├── infrastructure_defaults.json  # 新規追加
├── docker_defaults.json
├── languages.json
├── timeout.json
└── config.json
```

### 関連ドキュメント
- `src/configuration/README.md` - 設定システム使用方法
- `CLAUDE.md` - プロジェクト制約事項
- `scripts/quality_checks/getattr_checker.py` - 品質チェックツール

---

**最終更新**: 2024-06-22  
**承認者**: プロジェクトリード  
**実装期間**: 4-6日間  
**影響範囲**: Infrastructure層全体