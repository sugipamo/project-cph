# コマンドパース機能の実装

## 概要
Contest構造体に、与えられたコマンド文字列をパースし、コマンド種別と各パラメータを判定する機能を追加する。

## 現状の課題
- コマンド文字列のパース処理が各コマンドに分散している
- コマンドの構造がYAMLで定義されているが、その定義を活用できていない
- コマンドの曖昧性解決が実装されていない

## 実装方針

### 1. 新規モジュール作成
- `src/contest/parse.rs`を作成
- コマンドパース用の型定義と実装を分離

### 2. 型定義
```rust
#[derive(Debug, Clone)]
pub struct ParsedCommand {
    pub command_type: String,
    pub parameters: HashMap<String, String>,
}

#[derive(Debug)]
pub enum ParseError {
    NoMatch,
    MultipleMatches(Vec<String>),
    InvalidFormat(String),
}
```

### 3. 実装する機能
- コマンド文字列を受け取り、`ParsedCommand`を返す
- パースに失敗した場合は`ParseError`を返す
- 複数のコマンドにマッチする場合は候補を表示

### 4. アルゴリズム
1. コマンド文字列を空白で分割
2. commands.yamlの定義を読み込み
3. ordered/unorderedパターンとマッチング
4. マッチしたパターンからパラメータを抽出
5. 結果を返す

## 作業難易度
- 中程度
- 既存コードの変更は最小限
- テストの追加が必要

## 影響範囲
- Contest構造体
- CLI実装部分
- テストコード

## タスク
1. parse.rsの作成
2. 型定義の実装
3. パース機能の実装
4. テストの追加
5. Contest構造体への統合 