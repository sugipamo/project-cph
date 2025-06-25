# インフラストラクチャ層リファクタリング分析

## 概要
`__oldsrc/infrastructure`ディレクトリの分析結果として、大規模リファクタリングに必要となるコンポーネントを責務別に分類しました。

## 1. 実行抽象化層（Drivers）

### 責務
- 各種操作（シェルコマンド、Docker操作、ファイルI/O、Pythonコード実行）の抽象化レイヤー提供
- テンプレートメソッドパターンによる契約定義

### 必要コンポーネント
```
drivers/
├── base/
│   └── base_driver.py          # 全ドライバーの基底インターフェース
├── shell/
│   ├── shell_driver.py         # シェルコマンド実行の抽象
│   └── local_shell_driver.py   # ローカルシェル実装
├── docker/
│   ├── docker_driver.py        # Docker操作の抽象
│   └── docker_driver_with_tracking.py  # トラッキング機能付きDocker
├── file/
│   ├── file_driver.py          # ファイル操作の抽象
│   └── local_file_driver.py    # ローカルファイルシステム実装
├── python/
│   └── python_driver.py        # Pythonコード実行
└── unified/
    └── unified_driver.py       # 複数ドライバーの統合
```

## 2. 副作用分離層（Providers）

### 責務
- システムの副作用（ファイルI/O、プロセス実行、OS操作）の分離
- テスト可能性のためのモック可能インターフェース提供

### 必要コンポーネント
```
providers/
├── file_provider.py            # ファイルI/O操作（複雑なエラーハンドリングが必要）
├── sqlite_provider.py          # SQLiteデータベース操作（トランザクション管理が必要）
└── json_provider.py            # JSONシリアライズ/デシリアライズ（エラーハンドリング付き）
```

### 削除推奨（薄いラッパー）
以下のプロバイダーは単なるパススルーで価値を追加していないため削除推奨：
- `os_provider.py` - 標準の`os`モジュールを直接使用
- `sys_provider.py` - 標準の`sys`モジュールを直接使用  
- `time_provider.py` - 標準の`time`モジュールを直接使用
- `regex_provider.py` - 標準の`re`モジュールを直接使用

## 3. 設定管理層（Config）

### 責務
- アプリケーション設定の読み込みと管理
- 依存性注入の設定
- 実行時設定のオーバーレイ

### 必要コンポーネント
```
config/
├── config_loader_service.py    # 設定ファイルの読み込みとマージ
├── di_config.py                # DIコンテナ設定（遅延ロード）
└── runtime_config_overlay.py   # 実行時設定オーバーライド
```

## 4. 永続化層（Persistence）

### 責務
- SQLiteを使用したデータ永続化
- リポジトリパターンの実装

### 必要コンポーネント
```
persistence/
├── base/
│   └── base_repository.py      # リポジトリ基底クラス
├── sqlite/
│   ├── sqlite_manager.py       # DB接続と移行管理
│   ├── migrations/             # データベース移行スクリプト
│   └── repositories/
│       ├── operation_repository.py      # 操作履歴
│       ├── session_repository.py        # セッション管理
│       ├── docker_container_repository.py  # Dockerコンテナ追跡
│       └── system_config_repository.py     # システム設定
└── state/
    └── sqlite_state_repository.py  # アプリケーション状態管理
```

## 5. リクエスト/レスポンス層

### 責務
- コマンドパターンによる操作のカプセル化
- 構造化されたリクエスト/レスポンス処理

### 必要コンポーネント
```
requests/
├── base/
│   └── base_request.py         # リクエスト基底クラス
├── shell/
│   └── shell_request.py        # シェルコマンドリクエスト
├── docker/
│   └── docker_request.py       # Docker操作リクエスト
├── file/
│   └── file_request.py         # ファイル操作リクエスト
└── composite/
    └── composite_request.py    # 複合リクエスト

result/
├── base_result.py              # Result型の基本実装
├── result_factory.py           # Result生成ファクトリ
└── error_converter.py          # エラー変換ユーティリティ
```

## 6. 共通ユーティリティ

### 必要コンポーネント
```
├── di_container.py             # DIコンテナ実装
├── patterns/
│   └── retry_decorator.py      # リトライデコレータ
├── environment/
│   └── environment_manager.py  # 環境変数管理
└── debug/
    └── debug_service.py        # デバッグ支援
```

## アーキテクチャパターン

1. **依存性注入**: 遅延ロード付きDIコンテナ
2. **テンプレートメソッド**: 基底クラスでアルゴリズム定義、サブクラスで実装
3. **リポジトリパターン**: データ永続化の抽象化
4. **コマンドパターン**: リクエストオブジェクトによる操作カプセル化
5. **プロバイダーパターン**: 副作用の分離
6. **Result型パターン**: 明示的エラーハンドリング

## 設計原則

1. **副作用の分離**: 全I/O操作をプロバイダーに分離
2. **テスト可能性**: 全プロバイダーにモック実装
3. **明示的エラーハンドリング**: 例外ではなくResult型使用
4. **遅延ロード**: 必要時のみ依存関係をロード
5. **クリーンアーキテクチャ**: 抽象と実装の明確な分離

## リファクタリング推奨事項

1. **副作用の厳格な管理**: CLAUDE.mdに従い、副作用は`src/infrastructure`と`scripts/infrastructure`のみに制限
2. **デフォルト値の排除**: 全ての引数で明示的な値の指定を強制
3. **フォールバック処理の禁止**: エラーは明示的に処理
4. **設定管理の統一**: `src/configration/readme.md`に従った設定取得方法の実装
5. **依存性注入の徹底**: main.pyからの注入を徹底
6. **過度な抽象化の排除**: 
   - 薄いラッパーの削除（os、sys、time、regex プロバイダー）
   - 標準ライブラリの直接使用
   - 実際に価値を追加する抽象化のみ保持（ファイルI/O、DB操作など）

## 抽象化の判断基準

抽象化を作成する前に以下を確認：
1. **複雑なエラーハンドリングが必要か？**
2. **ビジネスロジックや変換処理があるか？**
3. **状態管理やトランザクション管理が必要か？**
4. **テスト時に本当にモックが必要か？**
5. **複数の実装が予想されるか？**

上記のいずれにも該当しない場合は、標準ライブラリを直接使用することを推奨。

この分析に基づいて、新しいインフラストラクチャ層を構築することで、中長期的な保守性と拡張性を確保できます。