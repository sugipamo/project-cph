date +%Y%m%d%H%M%Sを実行
git diff develop > agent/.refactor/yyyymmddhhmm_result.txt
を実行し、変更点を確認する。

もし、重要な機能を削除しているのであれば元に戻し、今回の作業結果を作成されたファイルに追記する
そうでなければ以下を行う
今回の作業結果を作成されたファイルに追記する、関数名などの変更があればメモしておく
feature/refactor_{}のブランチを作成し、コミット、プッシュする。
developブランチへのプルリクエストを作成する
git fetch を行う
developブランチへcheckoutする
developブランチへマージする
git fetch を行う
作成されたブランチを削除する