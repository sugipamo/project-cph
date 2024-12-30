use crate::error::Result;
use std::path::PathBuf;
use colored::*;
use std::process::Command;
use crate::cli::Site;
use std::env;

const OJ_TOOLS_DIR: &str = ".local/share/online-judge-tools";
const COOKIE_JAR_NAME: &str = "cookie.jar";
const CONTAINER_OJ_DIR: &str = "/workspace/.oj";

pub fn open_in_cursor(url: &str) -> Result<()> {
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

    fn setup_cookie_dir(&self) -> Result<(PathBuf, PathBuf)> {
        let cookie_path = dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join(OJ_TOOLS_DIR)
            .join(COOKIE_JAR_NAME);

        // cookie_pathをクローンして使用
        let cookie_dir = cookie_path.parent()
            .ok_or("Failed to get cookie directory")?
            .to_path_buf();

        // ディレクトリを作成
        std::fs::create_dir_all(&cookie_dir)?;

        // cookie.jarファイルを作成（存在しない場合）
        if !cookie_path.exists() {
            std::fs::write(&cookie_path, "")?;
        }

        Ok((cookie_path, cookie_dir))
    }

    async fn run_oj_command(&self, args: &[&str], mount_workspace: bool) -> Result<()> {
        let (_, cookie_dir) = self.setup_cookie_dir()?;
        let cookie_mount = format!("{}:{}", cookie_dir.display(), CONTAINER_OJ_DIR);
        let mut command = Command::new("docker");

        // 基本的なdockerコマンドを構築
        command.args(["run", "--rm", "-it"]);
        command.args(["-v", &cookie_mount]);

        // ワークスペースのマウントが必要な場合
        if mount_workspace {
            let workspace_mount = format!("{}:/workspace", self.workspace_path.display());
            command.args(["-v", &workspace_mount, "-w", "/workspace"]);
        }

        // OJコマンドを実行
        let status = command
            .args(["oj-container", "oj"])
            .args(args)
            .status()?;

        if !status.success() {
            return Err(format!("Command failed with status: {}", status).into());
        }

        Ok(())
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

        self.run_oj_command(&["login", site_url], false).await?;

        println!("{}", format!("Successfully logged in to {}", site.get_name()).green());
        Ok(())
    }

    pub async fn open(&self, problem: ProblemInfo) -> Result<()> {
        println!("{}", format!("Opening problem URL: {}", problem.url).cyan());
        println!("{}", format!("Please open this URL in your browser: {}", problem.url).yellow());

        let problem_test_dir = self.test_dir.join(&problem.problem_id);
        if problem_test_dir.exists() && has_test_cases(&problem_test_dir)? {
            println!("{}", "Test cases already exist, skipping download.".yellow());
            return Ok(());
        }

        let test_dir_relative = problem_test_dir.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative test directory")?;

        self.run_oj_command(&[
            "download",
            "-d", test_dir_relative.to_str().unwrap(),
            &problem.url,
        ], true).await?;

        println!("{}", "Problem setup completed".green());
        Ok(())
    }

    pub async fn submit(&self, problem: &ProblemInfo, _site: &Site, language_id: &str) -> Result<()> {
        println!("{}", format!("Submitting solution for problem {}...", problem.problem_id).cyan());

        let source_path_relative = problem.source_path.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative source path")?;

        self.run_oj_command(&[
            "submit",
            "--language", language_id,
            "--yes",
            &problem.url,
            source_path_relative.to_str().unwrap(),
        ], true).await?;

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