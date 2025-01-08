pub mod messages;

use anyhow::{Context, Result};

/// エラー結果にコンテキストを追加するためのトレイト
pub trait ResultExt<T> {
    fn with_context<C>(self, ctx: C) -> Result<T>
    where
        C: std::fmt::Display;
}

#[allow(clippy::disallowed_types)]
impl<T, E> ResultExt<T> for std::result::Result<T, E>
where
    E: std::error::Error + Send + Sync + 'static,
{
    fn with_context<C>(self, ctx: C) -> Result<T>
    where
        C: std::fmt::Display,
    {
        self.context(ctx)
    }
} 