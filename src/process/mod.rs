pub mod executor;
pub mod io;
pub mod limits;
pub mod monitor;
pub mod test;

pub use executor::{Process, Executor};
pub use io::Buffer;
pub use limits::Limits;
pub use monitor::{Monitor, Status};
pub use test::{Case, Outcome, Suite, Runner};

pub type Result<T> = anyhow::Result<T>; 