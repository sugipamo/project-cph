# 設定ガイド

## ファイル構造

```
.
├── active_contest/    # 現在作業中のコンテスト
│   ├── contests.yaml # コンテスト設定
│   ├── .moveignore  # 移動対象外ファイルの設定
│   ├── a/           # 問題Aのディレクトリ
│   │   ├── solution.{ext}  # 解答ファイル
│   │   ├── generator.{ext} # テストケース生成
│   │   └── test/    # テストケース
│   └── b/           # 問題Bのディレクトリ
│
├── contests/         # アーカイブされたコンテスト
│   └── abc001/      # コンテストごとのディレクトリ
│       └── a/       # 問題ごとのディレクトリ
│
└── contest_template/ # 言語別テンプレート
    ├── cpp/         # C++用テンプレート
    │   ├── solution.cpp
    │   └── generator.cpp
    ├── rust/        # Rust用テンプレート
    │   ├── solution.rs
    │   └── generator.rs
    └── pypy/        # PyPy用テンプレート
        ├── solution.py
        └── generator.py
```

## 設定ファイル

### contests.yaml

コンテストの基本設定を管理します：

```yaml
contest_id: "abc001"
language: "rust"  # 使用言語
site: "atcoder"   # 対象サイト
```

### .moveignore

`work`コマンド実行時に`contests`ディレクトリへ移動させないファイルを指定します：

```
# コメント行
contests.yaml  # 設定ファイル
.moveignore    # 移動対象外設定ファイル

# テンプレートファイル - コンテスト間で共有
template/
template/**
```

## テンプレートのカスタマイズ

### 言語別テンプレート

#### Rust (solution.rs)
```rust
use proconio::input;

fn main() {
    input! {
        n: usize,
    }
    
    println!("{}", n);
}
```

#### PyPy (solution.py)
```python
def main():
    n = int(input())
    print(n)

if __name__ == "__main__":
    main()
```

#### C++ (solution.cpp)
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    cout << n << endl;
    return 0;
}
```

### テンプレートの編集方法

1. `contest_template/{言語}/`ディレクトリ内の対応するファイルを編集
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
- C/C++
- YAML

### Cursor
追加の設定は不要です。 