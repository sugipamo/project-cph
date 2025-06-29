# Context層の処理概要

## 責務と役割

Context層は**Dockerfileの遅延読み込みとDocker名前生成機能**を担当する専門的な層です。主な責務は以下の通りです：

1. **Dockerfileコンテンツの遅延読み込み管理**
   - メインDockerfileとOJ（Online Judge）Dockerfileの遅延読み込み
   - ファイルアクセスの最適化とキャッシング機能
   - リソースアクセスの効率化

2. **Docker名前生成の統一管理**
   - 言語とDockerfileコンテンツに基づいたDocker名前生成
   - イメージ名とコンテナ名の一貫性保証
   - OJツール専用のDocker名前生成

3. **設定とリソースの結合点**
   - 設定システムとDockerリソースの橋渡し
   - 依存性注入パターンの実装

## ファイル別詳細分析

### `__init__.py`
- **役割**: モジュール初期化（循環依存回避のためimport無効化）
- **内容**: 循環依存を避けるため意図的にimportを無効化
- **設計意図**: Context層の独立性を保つ

### `dockerfile_resolver.py`
- **クラス**: `DockerfileResolver`
- **責務**: Dockerfileの遅延読み込みとDocker名前解決
- **主要メソッド**:
  - `dockerfile` (property): メインDockerfileの遅延読み込み
  - `oj_dockerfile` (property): OJ Dockerfileの遅延読み込み
  - `get_docker_names(language)`: Docker名前の統一生成
  - `invalidate_cache()`: キャッシュの無効化
  - `preload()`: 事前読み込み
  - `has_dockerfile()`, `has_oj_dockerfile()`: 設定確認

- **設計パターン**: 
  - **Lazy Loading Pattern**: プロパティアクセス時にファイル読み込み
  - **Caching Pattern**: 一度読み込んだ内容をキャッシュ
  - **Dependency Injection Pattern**: dockerfile_loaderとdocker_naming_providerを外部注入

- **エラーハンドリング**: 
  - ファイル読み込み失敗時のRuntimeError
  - プロバイダー未注入時のRuntimeError

### `oj.Dockerfile`
- **役割**: Online Judge用のDockerfile定義
- **内容**: 
  ```dockerfile
  FROM python:3.9
  RUN pip install --upgrade pip
  RUN pip install online-judge-tools
  RUN mkdir -p /workspace
  WORKDIR /workspace
  ```
- **用途**: OJツールの実行環境構築

## 依存関係とデータフロー

### 入力依存
1. **main.py**: 依存性注入による初期化
   - dockerfile_loader関数の注入
   - docker_naming_provider の注入
   - DockerfileパスとOJ Dockerfileパスの設定

2. **presentation/user_input_parser.py**: DockerfileResolverの利用
   - ExecutionConfig作成時のDocker名前解決
   - 設定システムとの連携

### 出力提供
1. **Docker名前辞書**: 
   ```python
   {
       "image_name": str,
       "container_name": str, 
       "oj_image_name": str,
       "oj_container_name": str
   }
   ```

2. **Dockerfileコンテンツ**: 文字列またはNone

### データフロー
```
main.py -> DockerfileResolver(injection) 
-> user_input_parser.py -> get_docker_names()
-> docker_naming_provider -> Docker名前生成
```

## 設計パターンと実装方針

### 採用パターン
1. **Resolver Pattern**: 設定システムと同じパターンでDockerfile解決
2. **Lazy Loading Pattern**: 必要になるまでファイル読み込みを遅延
3. **Dependency Injection Pattern**: 外部依存の注入による疎結合
4. **Caching Pattern**: パフォーマンス最適化のためのキャッシング

### 実装方針
1. **遅延読み込み**: リソースアクセスの最適化
2. **キャッシング**: 重複ファイル読み込みの防止
3. **エラーハンドリング**: 適切な例外メッセージでデバッグ支援
4. **型安全性**: Optional型による安全なNone処理

### パフォーマンス最適化
- プロパティベースの遅延読み込み
- 一度読み込んだ内容のキャッシング
- preload()メソッドでの明示的事前読み込み
- invalidate_cache()でのキャッシュ制御

## 注意事項とメンテナンス要点

### 重要な注意事項
1. **循環依存の回避**: `__init__.py`でimportを意図的に無効化
2. **依存性注入必須**: docker_naming_providerとdockerfile_loaderの注入が必要
3. **キャッシュ管理**: ファイル変更時は`invalidate_cache()`の呼び出しが必要

### メンテナンス要点
1. **テストカバレッジ**: 377行の包括的テストで品質保証
2. **エラーメッセージ**: デバッグ支援のための詳細なエラーメッセージ
3. **パフォーマンス**: 大量ファイル処理での遅延読み込み効果

### 互換性維持
- 既存の設定システムとの連携維持
- presentation層からの利用インターフェース安定性
- Docker名前生成の一貫性保証

### 拡張性
- 新しいDockerfile種別の追加可能
- 異なるDocker名前生成戦略への対応
- キャッシュ戦略のカスタマイズ可能

この設計により、Dockerfileの効率的な管理とDocker名前の一貫性が保たれ、システム全体のパフォーマンスと保守性が向上しています。