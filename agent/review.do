以下のコマンドを行う
date +%Y%m%d%H%M%S
tree -I 'agent|target' ./ >> agent/.review/yyyymmddhhmm_tree.txt
git diff develop >> agent/.review/yyyymmddhhmm_diff.txt
cargo check

txtnameを確認し、エラーを修正する

もしエラーがなければ以下を行う

もし、重要な機能を削除しているのであれば作業を中断、今回の作業結果を作成されたファイルに追記する

追加された機能が、すでに他で実装されているものではないか、プロジェクト内を確認する。重複しているのであれば、作業を中断。

追加された機能について、実装が非効率になっていないか確認する。非効率な点があれば、作業を中断。

可読性に問題はないか確認する。可読性に問題があれば、作業を中断。

今回の作業結果をagent/.review/yyyymmddhhmm_review.txtに記載

最後にコミットメッセージをテキストにはせず作成