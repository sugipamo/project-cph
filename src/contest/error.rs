use std::error::Error;
use crate::error::{CphError, ContestError};

pub fn site_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Contest(ContestError::Site(msg)))
}

pub fn language_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Contest(ContestError::Language(msg)))
}

pub fn config_err(msg: String) -> Box<dyn Error> {
    Box::new(CphError::Contest(ContestError::Config(msg)))
}
