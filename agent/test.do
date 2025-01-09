以下のコマンドを行う
date +%Y%m%d%H%M%S
tree -I 'agent|target' ./ >> agent/.test/yyyymmddhhmm_tree.txt
cargo clippy
cargo tarpaulin --out Html --output-dir coverage

実装計画をagent/.test/yyyymmddhhmm.mdに記述する