date +%Y%m%d%H%M%Sを実行
git diff develop > agent/.result/yyyymmddhhmm.txt
を実行し、変更点を確認する。

もし、重要な機能を削除しているのであれば作業を中断、今回の作業結果を作成されたファイルに追記する

cargo checkを行い、エラーがないか確認する。エラーがあれば、作業を中断し、今回の作業結果を作成されたファイルに追記する

追加された機能が、すでに他で実装されているものではないか、プロジェクト内を確認する。重複しているのであれば、作業を中断し、今回の作業結果を作成されたファイルに追記する

追加された機能について、実装が非効率になっていないか確認する。非効率な点があれば、作業を中断し、今回の作業結果を作成されたファイルに追記する

今回の作業結果を作成されたファイルに追記する
以下を行う
git add 
git commit -m "yyyymmddhhmm_{}"
git push