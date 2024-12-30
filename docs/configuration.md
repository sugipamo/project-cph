# 設定ガイド

## ファイル構造

```
.
├── contests/          # アーカイブされたコンテスト
│   └── abc001/
│       └── a.rs
├── contest_template/  # コンテスト用のテンプレート
│   └── template/     # 言語別テンプレート
│       ├── main.rs   # Rust用テンプレート
│       ├── main.py   # Python用テンプレート
│       └── template_gen.rs  # 生成スクリプトのテンプレート
└── src/              # 現在の問題ファイル
    ├── a.rs
    ├── contests.yaml # コンテスト設定
    ├── template/     # コピーされたテンプレート
    └── .moveignore   # 移動対象外ファイルの設定
```

## 設定ファイル

### contests.yaml

コンテストの基本設定を管理します：

```yaml
contest:
  id: "abc001"
  url: "https://atcoder.jp/contests/abc001"
  problems:
    - id: "a"
      url: "https://atcoder.jp/contests/abc001/tasks/abc001_a"
    - id: "b"
      url: "https://atcoder.jp/contests/abc001/tasks/abc001_b"

settings:
  language: "rust"  # デフォルトの言語
  template: "main.rs"  # デフォルトのテンプレート
  test:
    timeout: 30  # テストのタイムアウト（秒）
    memory_limit: 256  # メモリ制限（MB）
```

### .moveignore

`work`コマンド実行時に`contests`ディレクトリへ移動させないファイルを指定します：

```
# コメント行
template/      # テンプレートディレクトリ
contests.yaml  # 設定ファイル
.moveignore    # 移動対象外設定ファイル
```

## テンプレートのカスタマイズ

### 言語別テンプレート

#### Rust (main.rs)
```rust
use proconio::input;

fn main() {
    input! {
        n: usize,
    }
    
    println!("{}", n);
}
```

#### PyPy (main.py)
```python
def main():
    n = int(input())
    print(n)

if __name__ == "__main__":
    main()
```

### テンプレートの編集方法

1. `contest_template/template/`ディレクトリ内の対応するファイルを編集
2. 変更は次回の問題作成時から適用

## テスト設定

### メモリ制限の変更
`contests.yaml`で設定：
```yaml
settings:
  test:
    memory_limit: 512  # MB単位
```

### タイムアウトの変更
`contests.yaml`で設定：
```yaml
settings:
  test:
    timeout: 60  # 秒単位
```

## エディタ設定

### VSCode
推奨される拡張機能：
- rust-analyzer
- Python
- YAML

### Cursor
追加の設定は不要です。 