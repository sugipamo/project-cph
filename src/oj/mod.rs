use crate::error::Result;
use std::path::PathBuf;
use colored::*;
use std::process::Command;
use crate::cli::Site;
use std::env;
use crate::contest::Contest;
use crate::config::Config;
use users;
use std::os::unix::fs::PermissionsExt;
use dirs;

const COOKIE_DIR: &str = ".local/share/online-judge-tools";
const COOKIE_FILE: &str = "cookie.jar";
const DOCKERFILE_PATH: &str = "src/oj/Dockerfile";
const DOCKER_IMAGE_NAME: &str = "oj-container";

// エラーメッセージ
const ERROR_DOCKER_IMAGE_NOT_FOUND: &str = "Dockerイメージが見つかりません。'cargo run -- atcoder login'を実行してログインしてください。";
const ERROR_DOCKERFILE_NOT_FOUND: &str = "Dockerfile not found";

pub fn open_in_cursor(url: &str, source_path: Option<&PathBuf>) -> Result<()> {
    // 問題ページを開く
    if let Ok(browser) = env::var("BROWSER") {
        Command::new(&browser)
            .arg(url)
            .output()?;
    } else {
        println!("{}", format!("Note: To automatically open URLs, please set the $BROWSER environment variable.").yellow());
    }
    
    if let Err(e) = Command::new("code").arg(source_path.unwrap().display().to_string()).output() {
        println!("Note: Failed to open in VSCode: {}", e);
    }

    if let Err(e) = Command::new("cursor").arg(source_path.unwrap().display().to_string()).output() {
        println!("Note: Failed to open in Cursor: {}", e);
    }

    Ok(())
}

#[derive(Debug, Clone)]
pub struct ProblemInfo {
    pub url: String,
    pub source_path: PathBuf,
    pub problem_id: String,
}

pub struct OJContainer {
    workspace_path: PathBuf,
    contest: Contest,
}

impl OJContainer {
    pub fn new(workspace_path: PathBuf) -> Result<Self> {
        let contest = Contest::new(workspace_path.clone())?;
        Ok(Self { workspace_path, contest })
    }

    fn get_dockerfile_path() -> PathBuf {
        PathBuf::from(DOCKERFILE_PATH)
    }

    fn check_dockerfile_exists() -> Result<()> {
        if !Self::get_dockerfile_path().exists() {
            println!("{}", "Error: Dockerfile not found".red());
            return Err(ERROR_DOCKERFILE_NOT_FOUND.into());
        }
        Ok(())
    }

    fn get_cookie_paths() -> Result<(PathBuf, PathBuf)> {
        let home_dir = dirs::home_dir().ok_or("Failed to get home directory")?;
        let cookie_dir = home_dir.join(COOKIE_DIR);
        let cookie_path = cookie_dir.join(COOKIE_FILE);
        Ok((cookie_dir, cookie_path))
    }

    fn setup_cookie_file(cookie_dir: &PathBuf, cookie_path: &PathBuf) -> Result<()> {
        std::fs::create_dir_all(cookie_dir)?;
        std::fs::write(cookie_path, "#LWP-Cookies-2.0\n")?;
        std::fs::set_permissions(cookie_path, std::fs::Permissions::from_mode(0o600))?;
        Ok(())
    }

    async fn run_oj_command(&self, args: &[&str], mount_workspace: bool) -> Result<()> {
        let (_cookie_dir, cookie_path) = Self::get_cookie_paths()?;
        let mut command = Command::new("docker");

        // 基本的なdockerコマンドを構築
        let is_login = args.get(0).map_or(false, |&cmd| cmd == "login");
        if is_login {
            command.args(["run", "--rm", "-it"]);
        } else {
            command.args(["run", "--rm"]);
        }
        
        // ユーザーIDとグループIDを設定
        let uid = users::get_current_uid();
        let gid = users::get_current_gid();
        command.args(["-u", &format!("{}:{}", uid, gid)]);

        // 環境変数を設定
        command.args(["-e", &format!("HOME=/home/oj-user")]);

        // cookieファイルをコンテナ内の期待されるパスにマウント
        command.args(["-v", &format!("{}:/home/oj-user/{}/{}", cookie_path.display(), COOKIE_DIR, COOKIE_FILE)]);

        // ワークスペースのマウントが必要な場合
        if mount_workspace {
            let workspace_mount = format!("{}:/workspace", self.workspace_path.display());
            command.args(["-v", &workspace_mount, "-w", "/workspace"]);
        }

        // OJコマンドを実行
        let status = command
            .args([DOCKER_IMAGE_NAME, "oj"])
            .args(args)
            .status()?;

        if !status.success() {
            return Err(format!("Command failed with status: {}", status).into());
        }

        Ok(())
    }

    async fn check_image_exists(&self) -> Result<()> {
        let output = Command::new("docker")
            .args(["images", "-q", DOCKER_IMAGE_NAME])
            .output()?;

        if output.stdout.is_empty() {
            return Err(ERROR_DOCKER_IMAGE_NOT_FOUND.into());
        }

        Ok(())
    }

    pub async fn ensure_image(&self) -> Result<()> {
        Self::check_dockerfile_exists()?;
        println!("{}", "Building OJ container image...".cyan());

        let status = Command::new("docker")
            .args(["build", "-t", DOCKER_IMAGE_NAME, "-f", DOCKERFILE_PATH, "src/oj"])
            .status()?;

        if !status.success() {
            return Err("Failed to build docker image".into());
        }

        Ok(())
    }

    pub async fn login(&self, site: &Site) -> Result<()> {
        let site_url = site.get_url();
        println!("{}", format!("Logging in to {}...", site.get_name()).cyan());

        // cookieファイルをリセット
        println!("{}", "Resetting cookie file...".cyan());
        let (cookie_dir, cookie_path) = Self::get_cookie_paths()?;

        // cookieファイルが存在する場合は削除
        if cookie_path.exists() {
            std::fs::remove_file(&cookie_path)?;
        }

        // cookieファイルを作成
        Self::setup_cookie_file(&cookie_dir, &cookie_path)?;

        // Dockerイメージを再ビルド
        println!("{}", "Rebuilding Docker image...".cyan());
        Self::check_dockerfile_exists()?;

        let status = Command::new("docker")
            .args(["build", "--no-cache", "-t", DOCKER_IMAGE_NAME, "-f", DOCKERFILE_PATH, "src/oj"])
            .status()?;

        if !status.success() {
            return Err("Failed to build docker image".into());
        }

        // ログインを実行
        self.run_oj_command(&["login", site_url], false).await?;

        println!("{}", format!("Successfully logged in to {}", site.get_name()).green());
        Ok(())
    }

    pub async fn open(&self, problem: ProblemInfo) -> Result<()> {
        // 設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        println!("{}", format!("Opening problem URL: {}", problem.url).cyan());
        println!("{}", format!("Please open this URL in your browser: {}", problem.url).yellow());

        // Dockerイメージの存在確認
        self.check_image_exists().await?;

        // 問題ディレクトリのパスを取得
        let problem_dir = problem.source_path.parent()
            .ok_or_else(|| "Invalid problem path".to_string())?;

        // 問題ディレクトリを基準にコマンドを実行
        let relative_problem_dir = problem_dir.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative problem path")?;

        // テストディレクトリを設定から取得
        let test_dir = config.get::<String>("system.test.directory")
            .unwrap_or_else(|_| "test".to_string());

        self.run_oj_command(&[
            "download",
            "-d", &format!("{}/{}", relative_problem_dir.display(), test_dir),
            &problem.url,
        ], true).await?;

        println!("{}", "Problem setup completed".green());
        Ok(())
    }

    pub async fn submit(&self, problem: &ProblemInfo, site: &Site, language_id: &str) -> Result<()> {
        // 設定を取得
        let config = Config::builder()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

        println!("{}", format!("Submitting solution for problem {}...", problem.problem_id).cyan());

        // Dockerイメージの存在確認
        self.check_image_exists().await?;

        let source_path_relative = problem.source_path.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative source path")?;

        let mut args = vec![
            "submit",
            "--language", language_id,
        ];

        // 設定に基づいてコマンドライン引数を追加
        let wait = config.get::<u64>("system.submit.wait")
            .unwrap_or(0);
        let wait_arg = format!("--wait={}", wait);
        args.push(&wait_arg);

        let auto_yes = config.get::<bool>("system.submit.auto_yes")
            .unwrap_or(false);
        if auto_yes {
            args.push("--yes");
        }

        args.extend(&[
            &problem.url,
            source_path_relative.to_str().unwrap(),
        ]);

        self.run_oj_command(&args, true).await?;

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