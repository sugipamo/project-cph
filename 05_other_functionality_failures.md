# その他機能テスト失敗と修正計画

## 現在の失敗状況（2025年6月21日更新）

### 現在のテスト結果統計
- **FAILED**: 22テスト（引数不足によるTypeError、AssertionError）
- **PASSED**: 21テスト
- **合計**: 43テスト

### BaseRequest関連（FAILED - 8テスト）
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_init` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_set_name` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_debug_info_enabled` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_debug_info_disabled` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_execute_success` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_execute_without_driver_when_not_required` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_operation_type_property` - TypeError: missing 'operation_type'
- `tests/operations/test_base_request.py::TestOperationRequestFoundation::test_debug_info_stack_frame` - TypeError: missing 'operation_type'

### PythonRequest関連（FAILED - 6テスト）
- `tests/python/test_python_request.py::test_python_request_code_string` - AssertionError: stdout mismatch
- `tests/python/test_python_request.py::test_python_request_script_file` - AssertionError: stdout mismatch
- `tests/python/test_python_request.py::test_python_request_with_cwd` - AssertionError: stdout mismatch
- `tests/python/test_python_request.py::test_python_request_code_string_with_patch` - AssertionError: stdout mismatch
- `tests/python/test_python_request.py::test_python_request_script_file_with_patch` - AssertionError: stdout mismatch
- `tests/python/test_python_request.py::test_python_request_with_cwd_with_patch` - AssertionError: stdout mismatch

### DockerNaming関連（FAILED - 4テスト）
- `tests/unit/test_docker_naming_utils.py::TestGetDockerImageName::test_image_name_without_dockerfile` - TypeError: missing 'dockerfile_text'
- `tests/unit/test_docker_naming_utils.py::TestGetDockerContainerName::test_container_name_without_dockerfile` - TypeError: missing 'dockerfile_text'
- `tests/unit/test_docker_naming_utils.py::TestGetOjImageName::test_oj_image_name_without_dockerfile` - TypeError: missing 'oj_dockerfile_text'
- `tests/unit/test_docker_naming_utils.py::TestGetOjContainerName::test_oj_container_name_without_dockerfile` - TypeError: missing 'oj_dockerfile_text'

### RetryDecorator関連（FAILED - 4テスト）
- `tests/utils/test_retry_decorator.py::TestRetryConfig::test_default_config` - TypeError: missing 5 required arguments
- `tests/utils/test_retry_decorator.py::TestRetryConfig::test_custom_config` - TypeError: missing 3 required arguments
- `tests/utils/test_retry_decorator.py::TestRetryDecorator::test_successful_operation` - TypeError: missing 5 required arguments
- `tests/utils/test_retry_decorator.py::TestRetryableOperation::test_execute_with_retry_success` - TypeError: missing 5 required arguments

## 根本原因分析

### CLAUDE.mdルール適用による引数必須化と新たな問題
デフォルト値禁止ルールと実装の変更により以下の問題が発生：

1. **BaseRequest関連**
   - `BaseRequest.__init__()` で `operation_type` 引数が必須化
   - 全8テストで同じTypeError発生

2. **PythonRequest関連**
   - 引数不足ではなく、出力内容の不一致（AssertionError）
   - 期待される stdout と実際の stdout が異なる
   - パッチ適用の有無に関わらず全6テストで同じ問題

3. **DockerNaming関連**
   - `get_docker_image_name()`, `get_docker_container_name()` で `dockerfile_text` 引数が必須化
   - `get_oj_image_name()`, `get_oj_container_name()` で `oj_dockerfile_text` 引数が必須化

4. **RetryDecorator関連**
   - `RetryConfig.__init__()` で `max_attempts`, `base_delay`, `max_delay`, `backoff_factor`, `logger` の5引数が必須化
   - テストでの引数指定が不完全

## 修正計画

### Phase 1: BaseRequest系の修正（Critical - 8テスト）
- [ ] BaseRequestテスト: `operation_type` 引数を明示的に指定
- [ ] 全8テストでの初期化時 `operation_type` パラメータ追加
- [ ] テストファイル: tests/operations/test_base_request.py

### Phase 2: DockerNaming系の修正（High - 4テスト）
- [ ] DockerNamingUtilsテスト: `dockerfile_text` 引数を明示的に指定
- [ ] OJNamingUtilsテスト: `oj_dockerfile_text` 引数を明示的に指定
- [ ] テストファイル: tests/unit/test_docker_naming_utils.py

### Phase 3: RetryDecorator系の修正（High - 4テスト）
- [ ] RetryConfigテスト: 必須5引数 `max_attempts`, `base_delay`, `max_delay`, `backoff_factor`, `logger` を明示的に指定
- [ ] テストファイル: tests/utils/test_retry_decorator.py

### Phase 4: PythonRequest系の修正（Medium - 6テスト）
- [ ] PythonRequestテスト: stdout出力内容の期待値修正
- [ ] 実際の出力と期待値の差異調査
- [ ] パッチ適用時の動作確認・テスト条件見直し
- [ ] テストファイル: tests/python/test_python_request.py

### Phase 5: 包括的テストの実行
- [ ] 個別修正後の動作確認
- [ ] 関連機能の統合テスト
- [ ] 回帰テストの実施

## 修正の優先度と実装順序

### Critical（即時修正 - 8テスト）
1. **BaseRequest**: operation_type引数必須化への対応
   - 全8テストで同じTypeError
   - 基盤クラスのため他への影響大

### High（優先修正 - 8テスト）  
2. **DockerNaming**: dockerfile_text引数必須化への対応（4テスト）
3. **RetryDecorator**: 5引数必須化への対応（4テスト）

### Medium（中期修正 - 6テスト）
4. **PythonRequest**: stdout出力内容の期待値修正
   - AssertionErrorのため、ロジック調査が必要
   - 引数問題ではなく、出力内容の問題

### 修正パターンの分類

#### A. 引数必須化対応（18テスト）
- BaseRequest、DockerNaming、RetryDecorator
- CLAUDE.mdルール適用による典型的な問題
- テスト修正で解決可能

#### B. 出力内容不一致（6テスト）
- PythonRequest関連
- より複雑な問題、実装調査が必要

## 期待される修正結果
- **修正前**: 22個のFAILEDテスト
- **修正後**: 全テストPASS（22個 → 0個の失敗）
- **成功率**: 49% → 100%（21テスト成功 → 43テスト成功）

## 問題の特徴と新たな発見
- **主要原因**: CLAUDE.mdのデフォルト値禁止ルールによる引数必須化
- **新発見**: PythonRequestで出力内容不一致という新しいタイプの問題
- **影響範囲**: アプリケーションの基盤機能（Request処理、ユーティリティ）全般
- **修正パターン**: 引数明示化（18テスト）+ 出力検証修正（6テスト）