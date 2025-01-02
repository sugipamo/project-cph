# コマンドパース機能のテスト再構築

## 現状分析

### 実装の変更点
1. `NameResolver`構造体の導入
   - エイリアス解決機能の追加
   - 型ベースのパラメータ解決

2. `NameResolvers`構造体の導入
   - 複数のリゾルバの管理
   - コマンドパターンのマッチング機能

3. `ParsedCommand`構造体の変更
   - コマンド解析結果の保持

### テストに必要な要素

1. 基本機能テスト
   - リゾルバの初期化
   - エイリアス登録
   - 名前解決

2. コマンドパターンテスト
   - 順序付きパターンのマッチング
   - 順序なしパターンのマッチング
   - パターン不一致の検証

3. 設定ファイル連携テスト
   - YAMLファイルからの読み込み
   - パラメータ型の検証
   - コマンドパターンの検証

### テストケース例

1. コマンドパターンのテスト
```yaml
# テストケース1: 順序付きパターン
input: "atcoder test abc001 a"
expected:
  site_id: "atcoder"
  command: "test"
  contest_id: "abc001"
  problem_id: "a"

# テストケース2: 順序なしパターン
input: "abc001 test atcoder a"
expected:
  site_id: "atcoder"
  command: "test"
  contest_id: "abc001"
  problem_id: "a"

# テストケース3: エイリアス解決
input: "ac t abc001 a"
expected:
  site_id: "atcoder"
  command: "test"
  contest_id: "abc001"
  problem_id: "a"
```

2. エラーケース
```yaml
# テストケース4: 不正なパターン
input: "test"  # 必要なパラメータ不足
expected: Error

# テストケース5: 未知のエイリアス
input: "unknown test abc001-a"
expected: Error
```

## 実装方針

1. テストモジュール構成
```rust
#[cfg(test)]
mod tests {
    mod name_resolver {
        mod init;         // 初期化テスト
        mod alias;        // エイリアス解決テスト
        mod resolve;      // 名前解決テスト
    }
    mod command_pattern {
        mod ordered;      // 順序付きパターンテスト
        mod unordered;    // 順序なしパターンテスト
        mod errors;       // エラーケーステスト
    }
    mod integration {
        mod config;       // 設定ファイル連携テスト
        mod commands;     // コマンド実行テスト
    }
}
```

2. モックデータの準備
   - テスト用YAML設定
   ```yaml
   parameter_types:
     - name: command
       pattern: "command"
     - name: site_id
       pattern: "site"
   commands:
     test:
       aliases: ["test", "t"]
       ordered:
         - ["site_id", "command", "problem_id"]
   ```
   - サンプルコマンドパターン
   - テストケースマトリックス

## 作業難易度

- 基本機能テスト: 低
  - 単純な機能の検証
  - エイリアス解決のテスト

- パターンマッチングテスト: 中
  - 複雑なパターンの検証が必要
  - エッジケースの考慮
  - 順序付き/なしパターンの組み合わせ

- 統合テスト: 高
  - 設定ファイルとの連携
  - 実際のユースケースの検証
  - エラー処理の検証

## 次のステップ

1. テストディレクトリ構造の作成
2. モックデータの作成
   - テスト用YAML設定ファイル
   - テストケースの定義
3. 基本機能テストの実装
4. パターンマッチングテストの実装
5. 統合テストの実装
6. エラーケースの検証 