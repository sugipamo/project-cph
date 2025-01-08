ユーザー指示がなければ実装は行わない
date +%Y%m%d%H%M%Sを実行
tree -I 'agent|target' ./ を実行
必要なファイルを検索、実装計画をagent/.feature/yyyymmddhhmm.mdに記述する
cargo checkを行う
cargo clippyを行う
