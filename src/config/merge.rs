/// 設定ファイルのマージ機能を提供するトレイト
pub trait ConfigMerge {
    /// 他の設定をこの設定にマージする
    /// 
    /// # Arguments
    /// * `other` - マージする設定
    fn merge(&mut self, other: Self);
}

/// 基本的な型のマージ実装
impl ConfigMerge for String {
    fn merge(&mut self, other: Self) {
        *self = other;
    }
}

impl ConfigMerge for u32 {
    fn merge(&mut self, other: Self) {
        *self = other;
    }
}

impl ConfigMerge for bool {
    fn merge(&mut self, other: Self) {
        *self = other;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merge_string() {
        let mut base = "base".to_string();
        let other = "override".to_string();
        base.merge(other);
        assert_eq!(base, "override");
    }

    #[test]
    fn test_merge_u32() {
        let mut base = 0;
        let other = 42;
        base.merge(other);
        assert_eq!(base, 42);
    }

    #[test]
    fn test_merge_bool() {
        let mut base = false;
        let other = true;
        base.merge(other);
        assert_eq!(base, true);
    }
} 