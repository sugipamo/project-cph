fn generate_case() -> (String, String) {
    // TODO: カスタムケースの生成ロジックを実装
    let input = String::new();
    let output = String::new();
    (input, output)
}

fn main() {
    // 生成するテストケースの数を指定
    let n_cases = 1;
    
    let mut inputs = Vec::new();
    let mut outputs = Vec::new();
    
    for _ in 0..n_cases {
        let (input, output) = generate_case();
        inputs.push(input);
        outputs.push(output);
    }
    
    // 入力ケースの出力
    for input in inputs {
        println!("{}", input);
    }
    
    // 期待される出力の出力（標準エラー出力）
    for output in outputs {
        eprintln!("{}", output);
    }
}