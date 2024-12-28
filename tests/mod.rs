#[cfg(test)]
mod docker;

#[cfg(test)]
mod cli_test {
    use super::*;
    use std::process::Command;
    use std::path::PathBuf;
    use std::fs;
    use std::env;
    use assert_cmd::prelude::*;
    use predicates::prelude::*;
    use tempfile::tempdir;
} 