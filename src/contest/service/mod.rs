mod contest;
mod path;
mod test;
mod url;
mod command;

pub use contest::Service as ContestHandler;
pub use path::Service as PathHandler;
pub use test::Service as TestRunner;
pub use url::Service as UrlHandler;
pub use command::Service as CommandProcessor; 