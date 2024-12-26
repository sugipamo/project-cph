use clap::Parser;
use cph::{Config, Language, Command};

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Contest ID (e.g., abc300)
    contest_id: String,

    /// Programming language (rust/r or pypy/py)
    language: String,

    /// Command to execute (open/o, test/t, submit/s, or generate/g)
    command: String,

    /// Problem ID (e.g., a, b, c)
    problem_id: String,
}

fn main() {
    let args = Args::parse();

    let language = match Language::try_from(args.language.as_str()) {
        Ok(lang) => lang,
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    };

    let command = match Command::try_from(args.command.as_str()) {
        Ok(cmd) => cmd,
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    };

    let config = Config::new(
        args.contest_id,
        language,
        command,
        args.problem_id,
    );

    if let Err(e) = cph::run(config) {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}
