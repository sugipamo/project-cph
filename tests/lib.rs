mod docker;
mod helpers;

#[cfg(test)]
mod tests {
    use super::helpers::{setup, teardown};

    #[test]
    fn test_parse_ambiguous_commands() {
        setup();
        // テストの実行
        teardown();
    }
} 