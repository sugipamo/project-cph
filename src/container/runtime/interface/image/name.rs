use std::fmt;

/// イメージ名を表す構造体
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ImageName {
    /// レジストリ（例: "docker.io"）
    registry: Option<String>,
    /// リポジトリ（例: "library/nginx"）
    repository: String,
    /// タグ（例: "latest"）
    tag: Option<String>,
}

impl ImageName {
    /// 新しいイメージ名を作成します
    ///
    /// # Examples
    /// ```
    /// use container::runtime::interface::image::name::ImageName;
    /// let name = ImageName::new("nginx");
    /// assert_eq!(name.to_string(), "nginx:latest");
    /// ```
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            registry: None,
            repository: name.into(),
            tag: None,
        }
    }

    /// イメージ名をパースします
    ///
    /// # Examples
    /// ```
    /// use container::runtime::interface::image::name::ImageName;
    /// let name = ImageName::parse("docker.io/library/nginx:1.21").unwrap();
    /// assert_eq!(name.to_string(), "docker.io/library/nginx:1.21");
    /// ```
    pub fn parse(name: &str) -> Option<Self> {
        let mut parts = name.split('/');
        let last_part = parts.next_back()?;
        let mut repository_parts: Vec<_> = parts.collect();

        // タグの処理
        let (image_name, tag) = match last_part.split_once(':') {
            Some((name, tag)) => (name, Some(tag.to_string())),
            None => (last_part, Some("latest".to_string())),
        };
        repository_parts.push(image_name);

        // レジストリの判定
        let (registry, repository) = if repository_parts.len() > 1 
            && (repository_parts[0].contains('.') || repository_parts[0].contains(':')) {
            (Some(repository_parts.remove(0).to_string()), repository_parts.join("/"))
        } else {
            (None, repository_parts.join("/"))
        };

        Some(Self {
            registry,
            repository,
            tag,
        })
    }

    /// Docker形式のイメージ名を取得します
    pub fn to_docker_string(&self) -> String {
        self.to_string()
    }

    /// Containerd形式のイメージ名を取得します
    pub fn to_containerd_string(&self) -> String {
        let registry = self.registry.as_deref().unwrap_or("docker.io");
        let repository = if !self.repository.contains('/') {
            format!("library/{}", self.repository)
        } else {
            self.repository.clone()
        };
        let tag = self.tag.as_deref().unwrap_or("latest");
        format!("{}/{}", registry, repository)
    }

    /// イメージ名のバリデーションを行います
    ///
    /// # TODO
    /// - レジストリ名の形式チェック
    /// - リポジトリ名の禁止文字チェック
    /// - タグ名の形式チェック
    pub fn validate(&self) -> Result<(), String> {
        unimplemented!("イメージ名のバリデーション機能は未実装です")
    }

    /// イメージ名のダイジェスト形式を取得します
    ///
    /// # TODO
    /// - SHA256ダイジェストの追加
    /// - マルチプラットフォーム対応
    pub fn with_digest(&self, digest: &str) -> Self {
        unimplemented!("ダイジェスト形式の機能は未実装です")
    }

    /// イメージ名のバージョン比較を行います
    ///
    /// # TODO
    /// - セマンティックバージョニング対応
    /// - バージョン範囲指定
    pub fn compare_version(&self, other: &Self) -> std::cmp::Ordering {
        unimplemented!("バージョン比較機能は未実装です")
    }

    /// プラットフォーム固有のイメージ名を取得します
    ///
    /// # TODO
    /// - OS/アーキテクチャの指定
    /// - マニフェストリストの対応
    pub fn for_platform(&self, os: &str, arch: &str) -> Self {
        unimplemented!("プラットフォーム指定機能は未実装です")
    }
}

impl fmt::Display for ImageName {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if let Some(ref registry) = self.registry {
            write!(f, "{}/", registry)?;
        }
        write!(f, "{}", self.repository)?;
        if let Some(ref tag) = self.tag {
            write!(f, ":{}", tag)?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_name() {
        let name = ImageName::parse("nginx").unwrap();
        assert_eq!(name.repository, "nginx");
        assert_eq!(name.tag.as_deref(), Some("latest"));
        assert_eq!(name.registry, None);
    }

    #[test]
    fn test_parse_with_tag() {
        let name = ImageName::parse("nginx:1.21").unwrap();
        assert_eq!(name.repository, "nginx");
        assert_eq!(name.tag.as_deref(), Some("1.21"));
        assert_eq!(name.registry, None);
    }

    #[test]
    fn test_parse_with_registry() {
        let name = ImageName::parse("docker.io/library/nginx:latest").unwrap();
        assert_eq!(name.repository, "library/nginx");
        assert_eq!(name.tag.as_deref(), Some("latest"));
        assert_eq!(name.registry.as_deref(), Some("docker.io"));
    }

    #[test]
    fn test_format_conversion() {
        let name = ImageName::parse("nginx").unwrap();
        assert_eq!(name.to_docker_string(), "nginx:latest");
        assert_eq!(name.to_containerd_string(), "docker.io/library/nginx");
    }
} 