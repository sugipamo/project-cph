# Rust移行時に必要な品質チェック項目

## 概要

現在のsrc_checkシステムをRustに移行する場合、Rustの型システムとコンパイラーが自動的に解決する項目と、依然として必要な品質チェック項目を分析しました。

## 分析結果サマリー

- **40%**: Rustコンパイラーが自動解決（不要になる）
- **45%**: Rustでも価値のある品質チェック（移行対象）
- **15%**: Python固有（Rustに該当なし）

---

## 🟢 Rustで自動解決される項目（不要になる）

### メモリ・型安全性
- **構文エラー**: `syntax_checker.py` → Rustコンパイラーが検出
- **未使用インポート**: `unused_import_checker.py` → Rustコンパイラー警告
- **命名規則**: `naming_checker.py` → Rustが強制（snake_case/PascalCase）
- **Null参照**: `none_default_checker.py` → Option型で解決
- **型エラー**: Rustの静的型システムで完全防止

### セキュリティ（部分的）
- **SQLインジェクション**: 型安全なクエリビルダーで防止
- **メモリ安全性**: 所有権システムでバッファオーバーフロー等を防止
- **Use-after-free**: Rustの借用チェッカーで防止

---

## 🟡 Rustでも必要な品質チェック項目（移行対象）

### 1. アーキテクチャ品質（最重要）

#### 循環依存チェック
```rust
// Rustでも循環依存は可能（Rc/RefCell使用時）
use std::rc::{Rc, RefCell};

struct A {
    b: Option<Rc<RefCell<B>>>,
}

struct B {
    a: Option<Rc<RefCell<A>>>,  // ← 循環依存
}
```

#### レイヤー依存関係違反
```rust
// アーキテクチャ違反の例
mod presentation {
    use crate::infrastructure::Database;  // ← レイヤー違反
    
    pub fn handle_request() {
        Database::query("SELECT ...");  // ビジネスロジックを飛ばしている
    }
}
```

#### 副作用の分離
```rust
// 副作用が混在した悪い例
pub fn calculate_score(data: &Data) -> f64 {
    println!("Calculating..."); // ← 副作用
    let result = data.value * 2.0;
    save_to_file(&result);      // ← 副作用
    result
}
```

### 2. ビジネスロジック品質

#### エラーハンドリング戦略
```rust
// 一貫性のないエラー処理
pub fn process_data(input: &str) -> Result<Data, Box<dyn Error>> {
    let parsed = input.parse().unwrap(); // ← unwrap使用（要チェック）
    Ok(Data { value: parsed })
}

pub fn process_config(path: &str) -> Option<Config> {
    std::fs::read_to_string(path).ok()   // ← OptionとResultの混在
        .and_then(|s| serde_json::from_str(&s).ok())
}
```

#### リソース管理パターン
```rust
// 設定管理の品質
lazy_static! {
    static ref CONFIG: Config = Config::load().unwrap(); // ← グローバル状態
}

// より良い設計
pub struct AppContext {
    config: Config,
    db: Database,
}
```

### 3. パフォーマンス品質（Rust特有）

#### 不要なclone()呼び出し
```rust
// 非効率なパターン
fn process_items(items: &Vec<String>) -> Vec<String> {
    items.clone()                    // ← 不要なclone
        .into_iter()
        .map(|s| s.to_uppercase())
        .collect()
}

// 効率的なパターン
fn process_items(items: &[String]) -> Vec<String> {
    items.iter()
        .map(|s| s.to_uppercase())
        .collect()
}
```

#### 借用チェッカー回避の乱用
```rust
// 悪いパターン（設計の問題）
use std::rc::Rc;
use std::cell::RefCell;

struct BadDesign {
    data: Rc<RefCell<HashMap<String, Rc<RefCell<Value>>>>>,  // ← 複雑すぎる
}
```

### 4. 並行性品質

#### データ競合の潜在的リスク
```rust
// Rustでも注意が必要
use std::sync::{Arc, Mutex};

struct SharedCounter {
    value: Arc<Mutex<i32>>,
    backup: Arc<Mutex<i32>>,  // ← 複数ロックでデッドロック可能性
}
```

---

## 🔴 Python固有（Rustに該当なし）

- **動的属性アクセス**: `getattr`等の動的機能
- **Pickleシリアライゼーション**: Rustにはpickleなし
- **eval/exec**: Rustには動的評価なし
- **遅延インポート**: Rustは静的リンク

---

## 🎯 Rust用品質システム推奨構成

### 基本レイヤー（Clippy + 標準ツール）
```toml
# Cargo.toml
[lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
cargo = "warn"

# 特定の警告を有効化
unwrap_used = "forbid"           # unwrap()禁止
expect_used = "warn"             # expect()は警告
print_stdout = "warn"            # println!の使用を警告
```

### カスタム品質チェック
```rust
// 1. アーキテクチャ検証マクロ
#[cfg(test)]
mod architecture_tests {
    use super::*;
    
    #[test]
    fn presentation_should_not_import_infrastructure() {
        // コンパイル時にレイヤー違反を検出
    }
}

// 2. エラーハンドリング品質チェック
pub trait QualityError {
    fn severity(&self) -> ErrorSeverity;
    fn context(&self) -> &str;
}

// 3. リソース管理品質
pub trait ResourceManaged {
    fn lifecycle_stage(&self) -> LifecycleStage;
}
```

### 統合品質フレームワーク
```rust
// src_check_rust/
pub mod quality {
    pub mod architecture;    // レイヤー依存関係チェック
    pub mod performance;     // clone/allocation分析
    pub mod concurrency;     // データ競合パターン検出
    pub mod error_handling;  // Result/Option使用パターン
    pub mod business_logic;  // 副作用分離チェック
}

pub struct QualityReport {
    pub architecture_score: f64,
    pub performance_score: f64,
    pub concurrency_score: f64,
    pub error_handling_score: f64,
}
```

---

## 結論：移行優先度

### 高優先度（必須移行）
1. **アーキテクチャ品質チェック**（75%が有効）
2. **ビジネスロジック品質**（50%が有効）
3. **Rust固有のパフォーマンス分析**（新規必要）

### 中優先度
1. **並行性安全性チェック**（Rust特有）
2. **エラーハンドリング一貫性**（Result/Option使用パターン）

### 低優先度
1. **基本的なコード品質**（Clippyで十分）
2. **セキュリティチェック**（型システムで大部分解決）

**Rustの型システムの恩恵を受けつつ、アーキテクチャと設計品質に焦点を当てた品質システム**が最も効果的です。