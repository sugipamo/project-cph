以下のコマンドを行う
date +%Y%m%d%H%M%S

txtname = agent/.feature/yyyymmddhhmm.txt
tree . >> txtname
cargo check >> txtname
git diff develop >> txtname

txtnameを確認し、エラーを修正する