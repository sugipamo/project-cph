use crate::error::Result;
use std::path::PathBuf;
use colored::*;
use std::process::Command;
use std::env;
use users;
use std::os::unix::fs::PermissionsExt;
use dirs;
use crate::config::Config;

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
    
    if let Some(path) = source_path {
        if let Err(e) = Command::new("code").arg(path.display().to_string()).output() {
            println!("Note: Failed to open in VSCode: {}", e);
        }

        if let Err(e) = Command::new("cursor").arg(path.display().to_string()).output() {
            println!("Note: Failed to open in Cursor: {}", e);
        }
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
    site_name: String,
    config: Config,
}

impl OJContainer {
    pub fn new(workspace_path: PathBuf, site_name: String) -> Result<Self> {
        let config = Config::load()
            .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;
        Ok(Self { workspace_path, site_name, config })
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

    pub async fn login(&self) -> Result<()> {
        // サイトのURLを取得
        let url = self.config.get::<String>(&format!("sites.{}.url", self.site_name))?;
        let name = self.config.get::<String>(&format!("sites.{}.name", self.site_name))?;

        println!("{}", format!("Logging in to {}...", name).cyan());

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
        self.run_oj_command(&["login", &url], false).await?;

        println!("{}", format!("Successfully logged in to {}", name).green());
        Ok(())
    }

    pub async fn open(&self, problem: ProblemInfo) -> Result<()> {
        println!("{}", format!("Opening problem URL: {}", problem.url).cyan());

        // ブラウザ設定を確認
        let browser = self.config.get::<String>("system.browser")
            .or_else(|_| env::var("BROWSER"))
            .unwrap_or_else(|_| {
                println!("{}", format!("Note: To automatically open URLs, please set the $BROWSER environment variable or configure system.browser in config.yaml").yellow());
                String::new()
            });

        if !browser.is_empty() {
            if let Err(e) = Command::new(&browser).arg(&problem.url).output() {
                println!("Note: Failed to open in browser: {}", e);
            }
        }

        // エディタ設定を取得
        let editors = self.config.get::<Vec<String>>("system.editors")
            .unwrap_or_else(|_| vec!["code".to_string(), "cursor".to_string()]);

        // 各エディタで開く
        for editor in editors {
            if let Some(source_path) = problem.source_path.to_str() {
                if let Err(e) = Command::new(&editor).arg(source_path).output() {
                    println!("Note: Failed to open in {}: {}", editor, e);
                }
            }
        }

        // Dockerイメージの存在確認
        self.check_image_exists().await?;

        // 問題ディレクトリのパスを取得
        let problem_dir = problem.source_path.parent()
            .ok_or_else(|| "Invalid problem path".to_string())?;

        // 問題ディレクトリを基準にコマンドを実行
        let relative_problem_dir = problem_dir.strip_prefix(&self.workspace_path)
            .map_err(|_| "Failed to get relative problem path")?;

        // テストディレクトリを設定から取得
        let test_dir = self.config.get::<String>("system.test.directory")
            .unwrap_or_else(|_| "test".to_string());

        self.run_oj_command(&[
            "download",
            "-d", &format!("{}/{}", relative_problem_dir.display(), test_dir),
            &problem.url,
        ], true).await?;

        println!("{}", "Problem setup completed".green());
        Ok(())
    }

    pub async fn submit(&self, problem: &ProblemInfo, language_id: &str) -> Result<()> {
        // Dockerイメージの存在確認
        self.check_image_exists().await?;

        // 提出コマンドを実行
        println!("{}", format!("Submitting solution for problem {}...", problem.problem_id).cyan());

        self.run_oj_command(&[
            "submit",
            "-l", language_id,
            "-y",  // 確認をスキップ
            &problem.url,
            &problem.source_path.to_string_lossy(),
        ], true).await?;

        println!("{}", "Solution submitted successfully".green());
        Ok(())
    }
}

pub fn has_test_cases(dir: &PathBuf) -> Result<bool> {
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