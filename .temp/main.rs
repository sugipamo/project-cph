use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    let first_line = lines.next().unwrap().unwrap();
    let mut first_iter = first_line.split_whitespace();
    let n: usize = first_iter.next().unwrap().parse().unwrap();
    let a: i32 = first_iter.next().unwrap().parse().unwrap();
    let b: i32 = first_iter.next().unwrap().parse().unwrap();
    let second_line = lines.next().unwrap().unwrap();
    let c: Vec<i32> = second_line.split_whitespace().map(|x| x.parse().unwrap()).collect();
    let target = a + b;
    let pos = c.iter().position(|&x| x == target).unwrap() + 1;
    println!("{}", pos);
    println!("1");
}
