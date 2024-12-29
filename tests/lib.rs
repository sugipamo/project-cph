#[cfg(test)]
mod helpers;

#[cfg(test)]
mod docker;

#[cfg(test)]
mod tests {
    use super::helpers::{load_test_languages, setup_test_templates, cleanup_test_files};

    #[test]
    fn test_helpers() {
        let _lang_config = load_test_languages();
        setup_test_templates();
        cleanup_test_files();
    }
} 