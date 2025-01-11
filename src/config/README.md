# Config Module

YAMLベースの設定管理モジュールです。

## 使用方法

```rust
use crate::config::Config;

// 設定値の取得
let browser_id: i64 = Config::get("system.browser").unwrap();
let timeout: u64 = Config::get("system.timeout").unwrap();
```

## 設定ファイル

- `config.yaml`: システム全体の設定
- `commands.yaml`: コマンド定義

## 設定値の取得

ドット区切りのパスで設定値を取得できます：

```yaml
# config.yaml
system:
  browser: 1
  timeout: 30
```

上記の例では `system.browser` や `system.timeout` として値を取得できます。 