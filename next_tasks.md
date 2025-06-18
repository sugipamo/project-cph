# 次に行う予定の作業

## 現在の状況

**完了した作業**：
- ✅ env_jsonエラーの解決
- ✅ parallelエラーの解決  
- ✅ run_commandエラーの解決
- ✅ ワークフローステップ検出（7ステップ正常動作）
- ✅ 新設定システム（TypeSafeConfigNodeManager）への統一移行
- ✅ env_json依存の段階的廃止開始

**現在の問題**：
```
CompositeStepFailure: File operation failed: 'UnifiedDriver' object has no attribute 'copy'
```

## 次の作業：UnifiedDriverの機能実装

### 1. UnifiedDriverに不足しているメソッドの実装

**対象ファイル**: `src/infrastructure/drivers/unified/unified_driver.py`

**必要なメソッド**：
- `copy(source, destination)` - ファイル/ディレクトリコピー
- `move(source, destination)` - ファイル/ディレクトリ移動  
- `mkdir(path)` - ディレクトリ作成
- `rmtree(path)` - ディレクトリ削除
- `touch(path)` - ファイル作成
- `chmod(path, mode)` - 権限変更

**実装方針**：
```python
def copy(self, source: str, destination: str) -> Any:
    """ファイル/ディレクトリコピー操作"""
    file_driver = self.container.resolve("file_driver")
    # FileDriverのcopy機能を使用
    return file_driver.copy(source, destination)
```

### 2. FileDriverの機能確認・補強

**対象ファイル**: `src/infrastructure/drivers/file/local_file_driver.py`

**確認事項**：
- 各ファイル操作メソッドが実装されているか
- エラーハンドリングが適切か
- パス解決が正しく動作するか

### 3. WorkflowExecutionServiceの最適化

**対象ファイル**: `src/workflow/workflow_execution_service.py`

**実装済み改善点**：
- ✅ env_json依存の除去
- ✅ 新設定システムからのparallel設定取得
- ✅ 新設定システムからのworkflow steps取得

**残課題**：
- `_log_environment_info()`メソッドでまだenv_jsonに依存している部分の新設定システム移行

### 4. E2Eテストの完全動作確認

**対象ファイル**: `scripts/e2e.py`

**テストシナリオ**：
1. `./cph.sh abc300 open a python local` - 問題オープン
2. `./cph.sh test local` - テスト実行
3. `./cph.sh abc300 open a python docker` - Docker環境での動作

### 5. 設定システム移行の完了

**残作業**：
- `_log_environment_info()`の新設定システム移行
- レガシーenv_json参照の完全除去
- 互換性維持コメントの整理

## 優先順位

1. **高**: UnifiedDriverのcopyメソッド実装（E2E動作のブロッカー）
2. **高**: その他ファイル操作メソッドの実装
3. **中**: `_log_environment_info()`の新設定システム移行
4. **低**: レガシーコードの整理

## 期待される結果

これらの作業完了後：
- `scripts/e2e.py`が完全に動作
- 新設定システムへの移行完了
- env_json依存の完全廃止
- ファイル操作を含む全ワークフローの正常動作

## 技術債務

- UnifiedDriverの機能不足（今回で解決予定）
- env_json依存の段階的廃止（進行中）
- レガシーAPIとの互換性維持（計画的に対応）