use std::io;

fn main() {
    let mut input = String::new();
    io::stdin().read_line(&mut input).expect("Failed to read line");
    
    let nums: Vec<i32> = input
        .trim()
        .split_whitespace()
        .map(|s| s.parse().expect("Failed to parse number"))
        .collect();
    
    let sum = nums[0] + nums[1];
    println!("{}", sum);
}
