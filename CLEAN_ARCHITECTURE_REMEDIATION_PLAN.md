# クリーンアーキテクチャ修正計画

## 現状分析

### 主要な問題点

1. **レイヤー間依存関係違反**
   - Context層 → Operations層への不適切な依存
   - Configuration層 → Context層への不適切な依存
   - Operations層内に Infrastructure 関心事の混在

2. **副作用配置違反 (89件)**
   - Configuration、Context、Operations、Workflow層に副作用が散在
   - CLAUDE.mdルール違反: 副作用はInfrastructure層のみ許可

3. **依存性注入不備**
   - Infrastructure層サービスの直接インポート・使用
   - main.pyからの適切な依存性注入が未実装

## 修正戦略

### フェーズ1: 副作用の Infrastructure層への移行 (優先度: 高)

#### 1.1 Request オブジェクトの再配置
```
現在: src/operations/requests/* → Infrastructure層に移行
目標: src/infrastructure/requests/*
```

**対象ファイル:**
- `operations/requests/base/base_request.py`
- `operations/requests/docker/docker_request.py`
- `operations/requests/file/file_request.py`
- `operations/requests/python/python_request.py`
- `operations/requests/shell/shell_request.py`
- `operations/requests/composite/*`

**修正内容:**
1. Requestクラスを `src/infrastructure/requests/` に移動
2. Operations層に純粋なドメインインターフェースを作成
3. Infrastructure層でドメインインターフェースを実装

#### 1.2 Operations層の純粋化
```
作成対象: src/operations/interfaces/
- ExecutionInterface
- FileOperationInterface  
- DockerOperationInterface
- PythonOperationInterface
- ShellOperationInterface
```

### フェーズ2: レイヤー間依存関係の修正 (優先度: 高)

#### 2.1 Context層 → Operations層依存の解決

**問題ファイル:**
- `context/user_input_parser/user_input_parser.py:10-11`
- `context/formatters/context_formatter.py:8`

**修正方針:**
1. Context層で必要な機能をインターフェースとして定義
2. 実装をInfrastructure層に移動
3. 依存性注入でContext層に提供

#### 2.2 Configuration層の独立化

**問題ファイル:**
- `configuration/config_manager.py`

**修正方針:**
1. Configuration層をアプリケーション最下層に配置
2. 他層への依存を完全に排除
3. 純粋な設定データ構造のみ提供

### フェーズ3: 依存性注入の実装 (優先度: 中)

#### 3.1 main.py での依存性グラフ構築
```python
# 目標構造
def main():
    # Infrastructure層の初期化
    infrastructure_services = initialize_infrastructure()
    
    # Operations層への注入
    operations_services = initialize_operations(infrastructure_services)
    
    # Context層への注入
    context_services = initialize_context(operations_services)
    
    # Application層の実行
    app = Application(context_services)
    app.run()
```

#### 3.2 各層での依存性受け入れ体制構築
1. **Operations層**: インターフェースベースの依存性受け入れ
2. **Context層**: 必要な操作のインターフェース受け入れ
3. **Infrastructure層**: 外部依存の実装

### フェーズ4: Factory・Builder パターンの適用 (優先度: 低)

#### 4.1 Request Builder の作成
```
src/infrastructure/builders/
- DockerRequestBuilder
- FileRequestBuilder
- PythonRequestBuilder
- ShellRequestBuilder
```

#### 4.2 Operations Factory の修正
```
src/operations/factories/request_factory.py
→ 純粋なファクトリーインターフェースに変更
→ 実装はInfrastructure層で提供
```

## 実装順序

### 段階1: 緊急修正 (1-2日)
1. **副作用の移動**: Request クラスを Infrastructure層に移動
2. **インターフェース作成**: Operations層に純粋なインターフェース作成
3. **依存性注入**: main.pyでの基本的な注入体制構築

### 段階2: 構造修正 (3-5日)
1. **Context層の修正**: Operations層依存の排除
2. **Configuration層の独立化**: 他層依存の完全排除
3. **テスト修正**: 変更に伴うテストの更新

### 段階3: 最適化 (1-2日)
1. **Factory パターン適用**: より柔軟な生成パターンの実装
2. **エラーハンドリング強化**: 各層での適切なエラー処理
3. **パフォーマンス最適化**: 依存性注入のオーバーヘッド最小化

## 期待される効果

### 短期的効果
- ✅ クリーンアーキテクチャチェック通過
- ✅ CLAUDE.mdルール準拠
- ✅ テスト実行成功

### 中長期的効果
- 🔧 保守性の向上
- 🧪 テスタビリティの向上
- 🔄 変更容易性の向上
- 📈 コード品質の向上

## リスク管理

### 主要リスク
1. **大規模リファクタリングによる既存機能の破綻**
   - 対策: 段階的実装、テスト駆動開発

2. **依存性注入によるパフォーマンス劣化**
   - 対策: 適切な初期化タイミング、レイジーローディング

3. **複雑性の増加**
   - 対策: 明確なドキュメント、パターンの統一

### 回避策
- 各段階でのテスト実行確認
- 既存機能の動作確認
- 段階的ロールバック可能な実装

## 完了基準

### 必須条件
- [ ] ✅ クリーンアーキテクチャチェック通過
- [ ] ✅ 依存性注入チェック通過
- [ ] ✅ 副作用配置チェック通過
- [ ] ✅ 全テスト通過

### 品質条件
- [ ] 📋 各層の責務明確化
- [ ] 🔧 依存関係の単方向性確保
- [ ] 🧪 テストカバレッジ80%以上維持
- [ ] 📈 既存機能の完全動作確認

---

**注意事項:** 
- 本計画はCLAUDE.mdルールに完全準拠します
- 各段階での動作確認を必須とします
- 互換性維持のため段階的実装を行います