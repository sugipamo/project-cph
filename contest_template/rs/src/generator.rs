use rand::Rng;

fn main() {
    let mut rng = rand::thread_rng();
    let n = rng.gen_range(1..=100);
    
    println!("{}", n);
} 