# コマンドパース処理のConfig移行に関する調査

## 現状分析

### 設定ファイルの状況
- `src/config/config.yaml`にコマンドのエイリアス設定が既に存在
- コマンドごとに`aliases`が定義されている
- 設定ファイルは環境変数による上書きに対応

### コマンドパース処理の状況
- `src/cli/commands/mod.rs`でコマンドの生成と実行を管理
- `Command`トレイトによる共通インターフェース
- `CommandContext`による実行コンテキストの管理
- 各コマンドは個別のモジュールとして実装

### Contest構造体の状況
- `site_id`と`problem_id`の管理を担当
- コンテストに関する設定と状態管理が主な責務
- URLの生成やファイルパスの解決などのユーティリティ機能も提供

## 課題点
1. コマンドの定義が分散している
   - エイリアスは設定ファイルに存在
   - コマンド生成ロジックはコード内に存在
2. 拡張性の制限
   - 新規コマンド追加時に複数箇所の変更が必要
   - コマンドのオプションや振る舞いの設定が硬直的
3. 責務の混在
   - `CommandContext`が`site_id`と`problem_id`を管理
   - Contest構造体も同様の情報を管理
   - 情報の重複と責務の不明確さ

## 移行提案

### 方針1: 完全設定ファイル化
設定ファイルにコマンドの全定義を移動
```yaml
commands:
  test:
    aliases: ["t", "check"]
    handler: "TestCommand"
    requires:
      - site_id
      - problem_id
    options:
      timeout: 10
```

### 方針2: ハイブリッド方式
- 基本設定は設定ファイルで管理
- 実装詳細はコードで管理
- Factory パターンによる橋渡し
- Contest構造体からコンテキスト情報を取得

### 方針3: コンテキスト分離
```rust
// コンテキストの分離
pub struct ProblemContext {
    pub site_id: String,
    pub problem_id: String,
    pub contest_id: String,
}

pub struct CommandContext {
    pub problem: Option<ProblemContext>,
    pub config: Config,
}

impl CommandContext {
    pub fn from_contest(contest: &Contest) -> Self {
        // Contest構造体から必要な情報を抽出
    }
}
```

## 作業難易度
- 方針1: 🔴 高
  - 大規模なリファクタリングが必要
  - 型安全性の担保が課題
- 方針2: 🟡 中
  - 段階的な移行が可能
  - 既存コードの再利用が容易
- 方針3: 🟢 低
  - 既存のコードを活かしつつ責務を明確化
  - Contest構造体との連携が容易

## 推奨アプローチ
方針2と3の組み合わせを推奨
1. コンテキスト情報の分離（方針3）
2. 設定ファイルにコマンド定義を集約（方針2）
3. Factory パターンによるコマンド生成の整理（方針2）

## 次のステップ
1. ProblemContextの実装
2. CommandContextの再設計
3. コマンド定義の設定ファイルフォーマット確定
4. Factory パターン実装
5. 既存コマンドの段階的移行 