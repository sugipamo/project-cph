#include <bits/stdc++.h>
using namespace std;

class JudgeInterface {
private:
    int query_count;
    int max_queries;

public:
    JudgeInterface() : query_count(0), max_queries(100) {} // デフォルトのクエリ制限

    void set_max_queries(int max) {
        max_queries = max;
    }

    void output(const string& message) {
        cout << message << endl;
        cout.flush();
    }

    string input() {
        if (query_count >= max_queries) {
            wrong_answer("クエリ制限超過");
        }
        query_count++;
        
        string input;
        getline(cin, input);
        return input;
    }

    void correct_answer() {
        exit(0);
    }

    void wrong_answer(const string& message) {
        cerr << "Wrong Answer: " << message << endl;
        exit(1);
    }
};

int main() {
    JudgeInterface judge;
    // TODO: インタラクティブジャッジの実装
    // 例: 数当てゲーム
    int n = 42;
    judge.output("数当てゲームを開始します。1から100の数字を当ててください。");
    
    while (true) {
        string input = judge.input();
        try {
            int guess = stoi(input);
            if (guess == n) {
                judge.output("正解です！");
                judge.correct_answer();
            } else if (guess < n) {
                judge.output("もっと大きいです");
            } else {
                judge.output("もっと小さいです");
            }
        } catch (...) {
            judge.wrong_answer("不正な入力です");
        }
    }
    return 0;
} 