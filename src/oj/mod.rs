use crate::error::Result;
use std::path::PathBuf;
use colored::*;
use std::process::Command;
use crate::cli::Site;
use std::env;

fn open_in_cursor(url: &str) -> Result<()> {
    // BROWSER環境変数を確認
    if let Ok(browser) = env::var("BROWSER") {
        Command::new(&browser)
            .arg(url)
            .output()?;
        return Ok(());
    }

    // 環境変数が設定されていない場合は、URLを表示するだけ
    println!("{}", format!("Note: To automatically open URLs, please set the $BROWSER environment variable.").yellow());
    Ok(())
}

#[derive(Debug)]
pub struct ProblemInfo {
    pub url: String,
    pub source_path: PathBuf,
    pub problem_id: String,
}

pub struct OJContainer {
    workspace_path: PathBuf,
    test_dir: PathBuf,
}

impl OJContainer {
    pub fn new(workspace_path: PathBuf) -> Result<Self> {
        let test_dir = workspace_path.join("test");
        Ok(Self { workspace_path, test_dir })
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

    pub async fn login(&self, site: &Site) -> Result<()> {
        let site_url = site.get_url();
        println!("{}", format!("Logging in to {}...", site.get_name()).cyan());

        let cookie_path = dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join(".local/share/online-judge-tools/cookie.jar");

        let status = Command::new("docker")
            .args([
                "run",
                "--rm",
                "-it",
                "-v", &format!("{}:/root/.local/share/online-judge-tools/cookie.jar", cookie_path.display()),
                "oj-container",
                "oj",
                "login",
                site_url,
            ])
            .status()?;

        if !status.success() {
            println!("{}", format!("Error: Login to {} failed", site.get_name()).red());
            return Err("Failed to login".into());
        }

        println!("{}", format!("Successfully logged in to {}", site.get_name()).green());
        Ok(())
    }

    pub async fn open(&self, problem: ProblemInfo) -> Result<()> {
        println!("{}", format!("Opening problem URL: {}", problem.url).cyan());
        println!("{}", format!("Please open this URL in your browser: {}", problem.url).yellow());

        let cookie_path = dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join(".local/share/online-judge-tools/cookie.jar");

        let problem_test_dir = self.test_dir.join(&problem.problem_id);

        if problem_test_dir.exists() && has_test_cases(&problem_test_dir)? {
            println!("{}", "Test cases already exist, skipping download.".yellow());
            return Ok(());
        }

        println!("Workspace path: {}", self.workspace_path.display());
        println!("Source path: {}", problem.source_path.display());
        println!("Test directory: {}", problem_test_dir.display());

        let test_dir_relative = problem_test_dir.strip_prefix(&self.workspace_path)
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

    pub async fn submit(&self, problem: &ProblemInfo, _site: &Site, language_id: &str) -> Result<()> {
        println!("{}", format!("Submitting solution for problem {}...", problem.problem_id).cyan());

        let cookie_path = dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join(".local/share/online-judge-tools/cookie.jar");

        let source_path_relative = problem.source_path.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative source path")?;

        let output = Command::new("docker")
            .args([
                "run",
                "--rm",
                "-v", &format!("{}:/workspace", self.workspace_path.display()),
                "-v", &format!("{}:/root/.local/share/online-judge-tools/cookie.jar", cookie_path.display()),
                "-w", "/workspace",
                "oj-container",
                "oj",
                "submit",
                "--language", language_id,
                "--yes",
                &problem.url,
                source_path_relative.to_str().unwrap(),
            ])
            .output()?;

        if !output.status.success() {
            println!("{}", "Error: Submission failed".red());
            return Err("Failed to submit solution".into());
        }

        let output_str = String::from_utf8_lossy(&output.stdout);
        if let Some(url) = output_str
            .lines()
            .find(|line| line.contains("[SUCCESS] result:"))
            .and_then(|line| line.split(": ").nth(1))
        {
            println!("\n{}", "Submission successful!".green());
            println!("{}", "Your submission can be found at:".cyan());
            println!("{}", format!("  → {}", url).yellow());

            // URLを開く
            if let Err(e) = open_in_cursor(url) {
                println!("{}", format!("Note: Failed to open URL: {}.", e).yellow());
            }

            println!("");
        }

        println!("{}", "Solution submitted successfully".green());
        Ok(())
    }
}

fn has_test_cases(dir: &PathBuf) -> Result<bool> {
    if !dir.exists() {
        return Ok(false);
    }

    let entries = std::fs::read_dir(dir)?;
    let mut has_input = false;
    let mut has_output = false;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if let Some(extension) = path.extension() {
            if extension == "in" {
                has_input = true;
            } else if extension == "out" {
                has_output = true;
            }
        }
    }

    Ok(has_input && has_output)
} 