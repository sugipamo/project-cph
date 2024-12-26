use std::io::{self, Write};

fn generate_case() -> (String, String) {
    // TODO: カスタムケースの生成ロジックを実装
    let input = String::new();
    let output = String::new();
    (input, output)
}

fn main() {
    let (input, expected) = generate_case();
    
    // 入力ファイルの作成
    let mut input_file = std::fs::File::create("custom-1.in").unwrap();
    write!(input_file, "{}", input).unwrap();
    
    // 出力ファイルの作成
    let mut output_file = std::fs::File::create("custom-1.out").unwrap();
    write!(output_file, "{}", expected).unwrap();
    
    println!("Generated custom test case:");
    println!("Input:\n{}", input);
    println!("Expected output:\n{}", expected);
}