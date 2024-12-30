use std::io::{self, Write};

struct JudgeInterface {
    query_count: u32,
    max_queries: u32,
}

impl JudgeInterface {
    fn new() -> Self {
        Self {
            query_count: 0,
            max_queries: 100, // デフォルトのクエリ制限
        }
    }

    fn set_max_queries(&mut self, max_queries: u32) {
        self.max_queries = max_queries;
    }

    fn output(&self, message: &str) {
        println!("{}", message);
        io::stdout().flush().unwrap();
    }

    fn input(&mut self) -> String {
        if self.query_count >= self.max_queries {
            self.wrong_answer("クエリ制限超過");
        }
        self.query_count += 1;
        
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        input.trim().to_string()
    }

    fn correct_answer(&self) -> ! {
        std::process::exit(0);
    }

    fn wrong_answer(&self, message: &str) -> ! {
        eprintln!("Wrong Answer: {}", message);
        std::process::exit(1);
    }
}

fn main() {
    let mut judge = JudgeInterface::new();
    // TODO: インタラクティブジャッジの実装
    // 例: 数当てゲーム
    let n = 42;
    judge.output("数当てゲームを開始します。1から100の数字を当ててください。");
    
    loop {
        let input = judge.input();
        match input.parse::<i32>() {
            Ok(guess) => {
                if guess == n {
                    judge.output("正解です！");
                    judge.correct_answer();
                } else if guess < n {
                    judge.output("もっと大きいです");
                } else {
                    judge.output("もっと小さいです");
                }
            }
            Err(_) => judge.wrong_answer("不正な入力です"),
        }
    }
} 