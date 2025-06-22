# 互換性のために残されている関数一覧

このドキュメントは、コードベース内で互換性維持のために残されている関数や機能をまとめたものです。

## 1. Dockerラッパー関数（Legacy）

**ファイル**: `src/infrastructure/drivers/docker/legacy/docker_wrappers.py`

新しいDockerコマンドビルダーシステムへの移行における後方互換性を提供するラッパー関数群：

- `build_docker_run_command_wrapper` - Dockerコンテナ実行コマンド構築
- `build_docker_build_command_wrapper` - Dockerイメージビルドコマンド構築  
- `build_docker_stop_command_wrapper` - Dockerコンテナ停止コマンド構築
- `build_docker_remove_command_wrapper` - Dockerコンテナ削除コマンド構築
- `build_docker_ps_command_wrapper` - Dockerプロセス一覧コマンド構築
- `build_docker_inspect_command_wrapper` - Dockerコンテナ調査コマンド構築
- `build_docker_cp_command_wrapper` - Dockerファイルコピーコマンド構築
- `validate_docker_image_name_wrapper` - Dockerイメージ名検証

**目的**: 安定したインターフェースを提供しながら実際の実装に委譲

## 2. Dockerコマンドビルダーのレガシーエイリアス

**ファイル**: `src/infrastructure/drivers/docker/utils/docker_command_builder.py:379-388`

- `build_docker_run_command_legacy` - レガシー実行コマンド構築
- `build_docker_stop_command_legacy` - レガシー停止コマンド構築
- `build_docker_remove_command_legacy` - レガシー削除コマンド構築
- `build_docker_build_command_legacy` - レガシービルドコマンド構築
- `build_docker_ps_command_legacy` - レガシープロセス一覧コマンド構築
- `build_docker_inspect_command_legacy` - レガシー調査コマンド構築
- `build_docker_cp_command_legacy` - レガシーコピーコマンド構築
- `parse_container_names_legacy` - レガシーコンテナ名解析
- `validate_docker_image_name_legacy` - レガシーイメージ名検証

**目的**: 後方互換性エイリアス（レガシー関数バージョン）

## 3. フォーマッター関数の互換性エイリアス

**ファイル**: `src/operations/pure/formatters.py:146-148`

既存コードとの互換性のためのエイリアス：

- `format_string_legacy` → `format_string_simple`のエイリアス
- `safe_format_template` → `format_with_missing_keys`のエイリアス
- `extract_template_keys` → `extract_format_keys`のエイリアス

**目的**: 既存コードとの互換性維持

## 4. ステップランナーの互換性関数

**ファイル**: `src/workflow/step/step_runner.py:403-408`

- `check_when_condition` → `expand_when_condition`のエイリアス

**目的**: when条件をチェックする（互換性のため）

## 5. 設定管理での互換性維持

**ファイル**: `src/configuration/config_manager.py:52-56`

`TypedExecutionConfiguration`での内部実装でのオプショナルパラメータ取得

**目的**: 新設定システムへの移行時の互換性維持

## 6. Dockerドライバーの互換性メソッド

**ファイル**: `src/infrastructure/drivers/docker/docker_driver.py:77-78`

- `execute_command`メソッド

**目的**: BaseDriverとの互換性維持

## 7. 無効化されたアプリケーション互換性テスト

**ファイル**: `tests/cli/test_application_compatibility.py.disabled`

既存CLIApplicationとMinimalCLIAppの互換性テスト：
- 同じ引数で同じ動作をすることの確認
- エラーハンドリングの互換性確認
- インターフェースの互換性確認
- DIコンテナ使用の一貫性確認
- 後方互換性テスト
- 移行パステスト

**目的**: CLI アプリケーション間の互換性確認

## 8. Docker設定での互換性維持

**ファイル**: `src/infrastructure/drivers/docker/utils/docker_command_builder.py:77`

`.get()`使用の代替として設定システム経由でアクセス

**目的**: 新設定システムへの移行における互換性維持

## まとめ

このコードベースでは主に以下の領域で互換性維持機能が実装されています：

1. **Dockerコマンド操作**: 新コマンドビルダーシステムへの移行
2. **フォーマット機能**: 文字列フォーマット関数の新旧インターフェース
3. **設定システム**: 新設定システムへの移行
4. **CLI アプリケーション**: 新旧CLIアプリケーション間
5. **ステップ実行**: ワークフローステップ実行の条件チェック

これらの互換性機能により、システムの段階的な移行が可能になり、既存コードの動作を保証しながら新機能への移行を支援しています。