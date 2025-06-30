use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn example_benchmark(c: &mut Criterion) {
    c.bench_function("example", |b| {
        b.iter(|| {
            // ベンチマーク対象のコードをここに記述
            let sum: u32 = (0..1000).sum();
            black_box(sum);
        })
    });
}

criterion_group!(benches, example_benchmark);
criterion_main!(benches);