pub mod executor;
pub mod io;
pub mod limits;
pub mod monitor;
pub mod test;

pub use executor::{ProcessExecutor, Process};
pub use io::Buffer;
pub use monitor::ProcessStatus;
pub use test::{TestCase, TestResult, TestSuite};

pub type Result<T> = anyhow::Result<T>; 