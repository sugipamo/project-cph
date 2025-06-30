pub const SAMPLE_CONFIG: &str = r#"
[app]
name = "test-app"
version = "0.1.0"

[docker]
enabled = true
registry = "localhost:5000"

[test]
timeout = 30
language = "cpp"
"#;

#[allow(dead_code)]
pub const SAMPLE_WORKFLOW: &str = r#"
name: test-workflow
steps:
  - name: build
    command: cargo build
  - name: test
    command: cargo test
"#;

#[allow(dead_code)]
pub const SAMPLE_CPP_SOLUTION: &str = r#"
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
"#;

#[allow(dead_code)]
pub const SAMPLE_RUST_SOLUTION: &str = r#"
use std::io;

fn main() {
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let nums: Vec<i32> = input
        .trim()
        .split_whitespace()
        .map(|s| s.parse().unwrap())
        .collect();
    
    println!("{}", nums[0] + nums[1]);
}
"#;

#[allow(dead_code)]
pub const SAMPLE_PYTHON_SOLUTION: &str = r#"
a, b = map(int, input().split())
print(a + b)
"#;

#[allow(dead_code)]
pub struct TestCase {
    pub input: &'static str,
    pub expected_output: &'static str,
}

#[allow(dead_code)]
pub const TWO_SUM_TEST_CASES: &[TestCase] = &[
    TestCase { input: "1 2\n", expected_output: "3\n" },
    TestCase { input: "5 7\n", expected_output: "12\n" },
    TestCase { input: "-3 3\n", expected_output: "0\n" },
    TestCase { input: "100 200\n", expected_output: "300\n" },
];

#[allow(dead_code)]
pub fn get_sample_problem_config() -> String {
    r#"
{
    "name": "two-sum",
    "time_limit": 1.0,
    "memory_limit": 256,
    "test_cases": [
        {
            "input": "1 2\n",
            "output": "3\n"
        },
        {
            "input": "5 7\n",
            "output": "12\n"
        }
    ]
}
"#.to_string()
}