use std::error::Error;
use crate::error::CphError;

pub fn docker_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Docker(msg))
}

pub fn container_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Docker(format!("コンテナエラー: {}", msg)))
}

pub fn compilation_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Docker(format!("コンパイルエラー: {}", msg)))
}

pub fn command_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Docker(format!("コマンドエラー: {}", msg)))
}

pub fn state_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Docker(format!("状態エラー: {}", msg)))
} 