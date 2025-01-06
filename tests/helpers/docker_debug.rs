use std::path::Path;
use std::fs;

pub fn inspect_directory(dir: &Path) -> String {
    let mut result = String::new();
    result.push_str(&format!("Directory: {}\n", dir.display()));
    
    match fs::read_dir(dir) {
        Ok(entries) => {
            for entry in entries {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_file() {
                        result.push_str(&format!("File: {}\n", path.display()));
                        if let Ok(metadata) = fs::metadata(&path) {
                            result.push_str(&format!("  Size: {} bytes\n", metadata.len()));
                            result.push_str(&format!("  Permissions: {:?}\n", metadata.permissions()));
                        }
                    } else if path.is_dir() {
                        result.push_str(&format!("Directory: {}\n", path.display()));
                    }
                }
            }
        }
        Err(e) => {
            result.push_str(&format!("Error reading directory: {}\n", e));
        }
    }
    
    result
} 