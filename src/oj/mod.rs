use crate::error::Result;
use std::path::PathBuf;
use colored::*;
use std::process::Command;

#[derive(Debug)]
pub struct ProblemInfo {
    pub url: String,
    pub source_path: PathBuf,
    pub problem_id: String,
}

pub struct OJContainer {
    workspace_path: PathBuf,
}

impl OJContainer {
    pub fn new(workspace_path: PathBuf) -> Result<Self> {
        Ok(Self { workspace_path })
    }

    pub async fn ensure_image(&self) -> Result<()> {
        let dockerfile_path = PathBuf::from("src/oj/Dockerfile");
        if !dockerfile_path.exists() {
            println!("{}", "Error: Dockerfile not found".red());
            return Err("Dockerfile not found".into());
        }

        println!("{}", "Building OJ container image...".cyan());

        let status = Command::new("docker")
            .args(["build", "-t", "oj-container", "-f", "src/oj/Dockerfile", "src/oj"])
            .status()?;

        if !status.success() {
            return Err("Failed to build docker image".into());
        }

        Ok(())
    }

    pub async fn open(&self, problem: ProblemInfo) -> Result<()> {
        println!("{}", format!("Opening problem URL: {}", problem.url).cyan());
        println!("{}", format!("Please open this URL in your browser: {}", problem.url).yellow());

        let cookie_path = dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join(".local/share/online-judge-tools/cookie.jar");

        let test_dir = self.workspace_path.join("test").join(&problem.problem_id);
        if !test_dir.exists() {
            std::fs::create_dir_all(&test_dir)?;
        }

        println!("Workspace path: {}", self.workspace_path.display());
        println!("Source path: {}", problem.source_path.display());
        println!("Test directory: {}", test_dir.display());

        let test_dir_relative = test_dir.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative test directory")?;

        let status = Command::new("docker")
            .args([
                "run",
                "--rm",
                "-v", &format!("{}:/workspace", self.workspace_path.display()),
                "-v", &format!("{}:/root/.local/share/online-judge-tools/cookie.jar", cookie_path.display()),
                "-w", "/workspace",
                "oj-container",
                "oj",
                "download",
                "-d", test_dir_relative.to_str().unwrap(),
                &problem.url,
            ])
            .status()?;

        if !status.success() {
            println!("{}", "Error: Download failed".red());
            return Err("Failed to download test cases".into());
        }

        println!("{}", "Problem setup completed".green());
        Ok(())
    }
} 