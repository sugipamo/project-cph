# プロジェクト構造分析調査ログ

## 調査概要
- **調査日時**: 2025-01-31
- **対象**: /home/cphelper/project-cph
- **ソースファイル数**: 120個
- **テストファイル数**: 77個
- **調査観点**: フォルダ構造、命名規則、機能乖離、統一性

## 1. フォルダ構造分析

### 1.1 ルートレベル構成
```
project-cph/
├── 🟢 src/ (ソースコード)
├── 🟢 tests/ (テストコード)
├── 🟡 examples/ (サンプルコード)
├── 🟡 contest_* (コンテスト関連ディレクトリ)
├── 🟡 workspace/ (作業用ディレクトリ)
├── 🔴 target/ (Rustビルド成果物)
└── 🟢 設定ファイル群
```

**評価**:
- ✅ `src/`と`tests/`の分離は適切
- ⚠️ コンテスト関連ディレクトリが複数散在（`contest_current/`, `contest_stock/`, `contest_template/`）
- ❌ `target/`ディレクトリが存在するがRust用途が不明瞭

### 1.2 src/配下の構造分析

#### 🟢 **適切に配置されているモジュール**
```
src/
├── context/ (実行コンテキスト関連)
├── operations/ (操作・リクエスト処理)
├── utils/ (汎用ユーティリティ)
└── main.py (エントリーポイント)
```

#### 🟡 **改善の余地があるモジュール**
```
src/env/ (環境関連 - 肥大化傾向)
├── factory/ (14個のファクトリクラス)
├── resource/ (リソース管理)
├── step/ (ステップ実行)
├── step_generation/ (ステップ生成)
├── fitting/ (環境適合)
├── workflow/ (ワークフロー)
├── env_workflow_service.py
├── env_resource_controller.py
└── その他
```

## 2. 命名規則の一貫性分析

### 2.1 ✅ **統一されている命名パターン**

#### ファイル命名
- **テストファイル**: `test_*.py` (77個すべて統一)
- **基底クラス**: `base_*.py` 形式
- **ファクトリクラス**: `*_command_request_factory.py` 形式
- **ハンドラクラス**: `*_handler.py` 形式

#### クラス命名
- **ファクトリ**: `*CommandRequestFactory`
- **リクエスト**: `*Request`
- **ドライバー**: `*Driver`
- **ハンドラー**: `*Handler`

### 2.2 ⚠️ **改善が必要な命名**

#### 略語の不統一
- `env` vs `environment` (混在)
- `config` vs `configuration` (混在)
- `req` vs `request` (混在)

#### 言語混在
- 英語: `ExecutionContext`, `DIContainer`
- 日本語コメント: `"""実行コンテキスト"""`
- パス名: 日本語が含まれる可能性

## 3. 機能と名前の乖離チェック

### 3.1 🔴 **機能乖離の問題**

#### `src/env/` の責務過多
```
env/ (環境関連のはずが...)
├── factory/ (リクエスト生成)
├── step/ (ステップ実行)
├── step_generation/ (ステップ生成)
├── workflow/ (ワークフロー管理)
└── fitting/ (環境適合)
```
**問題**: 「環境」という名前だが、実際はワークフロー全体の管理を担当

#### `src/operations/` との役割重複
```
operations/ (操作関連)
├── composite/ (複合リクエスト)
├── file/ (ファイル操作)
├── shell/ (シェル操作)
└── factory/ (ドライバーファクトリ)

env/factory/ (環境側のファクトリ)
├── 14個のコマンドファクトリ
```
**問題**: ファクトリが2箇所に分散

### 3.2 🟡 **名前が機能を適切に表していない例**

- `run_step_*.py`: 実際は「実行」ではなく「ステップ定義」
- `env_workflow_service.py`: 環境固有ではなく汎用ワークフローサービス
- `pure_functions.py`: 場所が `operations/utils/` で違和感

## 4. モジュール間の結合度分析

### 4.1 🔴 **高結合の問題箇所**

#### `src/env/factory/` (14個のファクトリ)
```python
# 全ファクトリが同様の構造
class MkdirCommandRequestFactory(BaseCommandRequestFactory):
class CopyCommandRequestFactory(BaseCommandRequestFactory):
class TouchCommandRequestFactory(BaseCommandRequestFactory):
# ... 11個以上
```
**問題**: コード重複率が高く、保守性が低い

#### 循環依存の可能性
- `env/` ← → `operations/` 間の相互参照
- `context/` → `env/` → `context/` の循環

### 4.2 🟢 **適切に分離されている部分**

- `src/utils/` - 他モジュールから独立
- `tests/` - ソースと明確に分離
- `src/context/resolver/` - 責務が明確

## 5. 改善提案

### 5.1 🚨 **高優先度: 構造的改善**

#### A. `src/env/` の分割再編
```
現在: src/env/ (巨大な単一モジュール)
提案: 
├── src/workflow/ (ワークフロー関連)
├── src/environment/ (環境適合関連)
├── src/execution/ (実行制御関連)
└── src/generation/ (ステップ生成関連)
```

#### B. ファクトリ統合
```
現在: 14個の個別ファクトリクラス
提案: 
├── CommandRequestFactory (統合ファクトリ)
├── command_types.py (コマンド種別定義)
└── request_builders/ (個別ビルダー)
```

### 5.2 🟡 **中優先度: 命名統一**

#### A. 略語統一ルール
- `environment` → `env` (一律短縮)
- `configuration` → `config` (一律短縮)
- `request` → そのまま (短縮しない)

#### B. 言語統一
- コメント: 英語に統一
- 変数名: 英語に統一
- パス: ASCII文字のみ

### 5.3 🟢 **低優先度: 細かい改善**

#### A. ディレクトリ整理
```
現在: contest_current/, contest_stock/, contest_template/
提案: contests/ 配下に統合
```

#### B. 設定ファイル整理
- `requirements.txt` 追加
- `pyproject.toml` 検討

## 6. リファクタリング優先度

### Phase 1 (即実施) 🔴
1. **ファクトリクラス統合** - 14→3クラスに削減
2. **`src/env/` 分割** - 責務明確化
3. **テストカバレッジ0%モジュール対応**

### Phase 2 (短期) 🟡  
1. **命名規則統一** - 略語・言語の標準化
2. **循環依存解消** - モジュール構造見直し
3. **ドキュメント整備**

### Phase 3 (長期) 🟢
1. **コンテストディレクトリ統合**
2. **設定ファイル標準化**
3. **型ヒント完全対応**

## 7. 結論

### 現状評価
- **健全性**: 🟡 (テストは充実、構造に改善余地)
- **保守性**: 🟡 (ファクトリ重複、env肥大化)
- **拡張性**: 🟢 (基盤は良好、設計パターン適用済み)

### 最優先課題
1. `src/env/` の責務分割とモジュール再編
2. 14個のファクトリクラスの統合
3. テストカバレッジ0%の解消

**この構造分析により、フォルダ構造から機能を把握しやすくするための具体的な改善方針が明確になりました。**