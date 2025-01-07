以下のコマンドを行う
date +%Y%m%d%H%M%S
tree . >> agent/.fix-errors/yyyymmddhhmm_tree.txt
cargo check >> agent/.fix-errors/yyyymmddhhmm_check.txt
git diff develop >> agent/.fix-errors/yyyymmddhhmm_diff.txt

txtnameを確認し、エラーを修正する