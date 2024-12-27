use std::io::*;

fn main() {
    let mut input = String::new();
    stdin().read_line(&mut input).unwrap();
    let mut iter = input.split_whitespace();
    let n: usize = iter.next().unwrap().parse().unwrap();
    let a: usize = iter.next().unwrap().parse().unwrap();
    let b: usize = iter.next().unwrap().parse().unwrap();

    let mut input = String::new();
    stdin().read_line(&mut input).unwrap();
    let c: Vec<usize> = input.split_whitespace()
        .map(|x| x.parse().unwrap())
        .collect();

    println!("{}", c[a + b - 2]); // 0-basedインデックスに調整
} 