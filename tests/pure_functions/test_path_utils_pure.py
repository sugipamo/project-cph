"""
パス操作純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
from pathlib import Path
import os
from src.pure_functions.path_utils_pure import (
    PathInfo,
    PathResolutionResult,
    SafePathResult,
    resolve_path_pure,
    normalize_path_pure,
    get_relative_path_pure,
    is_subdirectory_pure,
    safe_path_join_pure,
    get_file_extension_pure,
    change_extension_pure,
    analyze_path_structure_pure,
    find_common_parent_pure,
    validate_path_security_pure,
    generate_path_variations_pure,
    calculate_path_metrics_pure
)


class TestPathInfo:
    """PathInfoのテスト"""
    
    
    
    def test_path_info_from_path(self):
        """パスからのPathInfo作成テスト"""
        # 相対パスでテスト（存在チェックを避ける）
        test_path = "subdir/test_file.py"
        info = PathInfo.from_path(test_path)
        
        assert info.name == "test_file.py"
        assert info.stem == "test_file"
        assert info.suffix == ".py"
        assert info.parent == "subdir"


class TestPathResolutionResult:
    """PathResolutionResultのテスト"""
    
    def test_create_resolution_result(self):
        """パス解決結果作成のテスト"""
        result = PathResolutionResult(
            resolved_path="/resolved/path",
            is_relative=False,
            resolution_method="absolute_path",
            errors=[],
            warnings=[]
        )
        
        assert result.resolved_path == "/resolved/path"
        assert result.is_relative is False
        assert result.resolution_method == "absolute_path"
    
    def test_resolution_result_defaults(self):
        """解決結果のデフォルト値テスト"""
        result = PathResolutionResult(
            resolved_path="test",
            is_relative=True,
            resolution_method="test",
            errors=None,
            warnings=None
        )
        
        assert result.errors == []
        assert result.warnings == []


class TestResolvePathPure:
    """パス解決関数のテスト"""
    
    def test_resolve_absolute_path(self):
        """絶対パス解決のテスト"""
        result = resolve_path_pure("/base/dir", "/absolute/path")
        
        assert result.resolved_path == "/absolute/path"
        assert result.is_relative is False
        assert result.resolution_method == "absolute_path"
        assert len(result.errors) == 0
    
    def test_resolve_relative_path(self):
        """相対パス解決のテスト"""
        result = resolve_path_pure("/base/dir", "relative/path")
        
        expected = str(Path("/base/dir") / "relative/path")
        assert result.resolved_path == expected
        assert result.is_relative is True
        assert result.resolution_method == "relative_to_base"
        assert len(result.errors) == 0
    
    def test_resolve_path_with_pathlib_objects(self):
        """Pathlibオブジェクトでの解決テスト"""
        base = Path("/base/dir")
        target = Path("sub/file.txt")
        
        result = resolve_path_pure(base, target)
        
        expected = str(base / target)
        assert result.resolved_path == expected
        assert result.is_relative is True
    
    def test_resolve_path_error_handling(self):
        """パス解決エラーハンドリングのテスト"""
        # 無効なパスでエラーをテスト（非常に長いパスなど）
        very_long_path = "a" * 1000
        result = resolve_path_pure("/base", very_long_path)
        
        # エラーが起きても安全に処理される
        assert result.resolved_path is not None


class TestNormalizePathPure:
    """パス正規化関数のテスト"""
    
    def test_normalize_simple_path(self):
        """シンプルなパス正規化のテスト"""
        result = normalize_path_pure("./test/../file.txt")
        
        assert "file.txt" in result.resolved_path
        assert result.resolution_method == "normalize"
        assert len(result.errors) == 0
    
    def test_normalize_absolute_path(self):
        """絶対パス正規化のテスト"""
        # ルートから始まる絶対パスをテスト
        result = normalize_path_pure("/tmp/../etc/hosts")
        
        assert result.resolved_path.endswith("etc/hosts")
        assert result.resolution_method == "normalize"
    
    def test_normalize_path_error_handling(self):
        """正規化エラーハンドリングのテスト"""
        # Noneや無効な型でエラーテスト
        result = normalize_path_pure("")
        
        # エラーが起きても安全に処理される
        assert result.resolved_path is not None


class TestGetRelativePathPure:
    """相対パス取得関数のテスト"""
    
    def test_get_relative_path_success(self):
        """相対パス取得成功のテスト"""
        result = get_relative_path_pure("/base/dir", "/base/dir/sub/file.txt")
        
        assert result.resolved_path == "sub/file.txt"
        assert result.is_relative is True
        assert result.resolution_method == "relative_to"
        assert len(result.errors) == 0
    
    def test_get_relative_path_fallback(self):
        """相対パス取得フォールバックのテスト"""
        result = get_relative_path_pure("/base/dir", "/completely/different/path")
        
        assert "/completely/different/path" in result.resolved_path
        assert result.is_relative is False
        assert result.resolution_method == "absolute_fallback"
        assert len(result.warnings) >= 1
    
    def test_get_relative_path_same_directory(self):
        """同じディレクトリの相対パステスト"""
        result = get_relative_path_pure("/base/dir", "/base/dir")
        
        assert result.resolved_path == "."
        assert result.is_relative is True


class TestIsSubdirectoryPure:
    """サブディレクトリ判定関数のテスト"""
    
    def test_is_subdirectory_true(self):
        """サブディレクトリ判定Trueのテスト"""
        is_sub, errors = is_subdirectory_pure("/parent", "/parent/child/subdir")
        
        assert is_sub is True
        assert len(errors) == 0
    
    def test_is_subdirectory_false(self):
        """サブディレクトリ判定Falseのテスト"""
        is_sub, errors = is_subdirectory_pure("/parent", "/different/path")
        
        assert is_sub is False
        assert len(errors) == 0
    
    def test_is_subdirectory_same_path(self):
        """同じパスでのサブディレクトリ判定テスト"""
        is_sub, errors = is_subdirectory_pure("/path", "/path")
        
        assert is_sub is True  # 同じパスはサブディレクトリとみなす
        assert len(errors) == 0
    
    def test_is_subdirectory_relative_paths(self):
        """相対パスでのサブディレクトリ判定テスト"""
        is_sub, errors = is_subdirectory_pure("parent", "parent/child")
        
        assert is_sub is True
        assert len(errors) == 0


class TestSafePathJoinPure:
    """安全なパス結合関数のテスト"""
    
    def test_safe_path_join_success(self):
        """安全なパス結合成功のテスト"""
        result = safe_path_join_pure("base", "sub", "file.txt")
        
        assert result.is_safe is True
        assert "base" in result.path
        assert "sub" in result.path
        assert "file.txt" in result.path
        assert len(result.security_issues) == 0
    
    def test_safe_path_join_traversal_attack(self):
        """パストラバーサル攻撃の検出テスト"""
        result = safe_path_join_pure("base", "..", "etc", "passwd")
        
        assert result.is_safe is False
        assert result.path is None
        assert len(result.security_issues) >= 1
        assert any("parent directory" in issue for issue in result.security_issues)
    
    def test_safe_path_join_absolute_path(self):
        """絶対パスの検出テスト"""
        result = safe_path_join_pure("base", "/absolute/path")
        
        assert result.is_safe is False
        assert result.path is None
        assert any("absolute" in issue for issue in result.security_issues)
    
    def test_safe_path_join_empty_input(self):
        """空入力のテスト"""
        result = safe_path_join_pure()
        
        assert result.is_safe is False
        assert result.path is None
        assert "No paths provided" in result.security_issues
    
    def test_safe_path_join_single_path(self):
        """単一パスの結合テスト"""
        result = safe_path_join_pure("single_path")
        
        assert result.is_safe is True
        assert result.path == "single_path"


class TestFileExtensionFunctions:
    """ファイル拡張子関数のテスト"""
    
    def test_get_file_extension(self):
        """ファイル拡張子取得のテスト"""
        assert get_file_extension_pure("file.txt") == ".txt"
        assert get_file_extension_pure("archive.tar.gz") == ".gz"
        assert get_file_extension_pure("no_extension") == ""
        assert get_file_extension_pure(".hidden") == ""
        assert get_file_extension_pure(".hidden.txt") == ".txt"
    
    def test_change_extension_with_dot(self):
        """ドット付き拡張子変更のテスト"""
        result = change_extension_pure("file.txt", ".py")
        
        assert result.resolved_path == "file.py"
        assert result.resolution_method == "extension_change"
        assert len(result.errors) == 0
    
    def test_change_extension_without_dot(self):
        """ドットなし拡張子変更のテスト"""
        result = change_extension_pure("file.txt", "py")
        
        assert result.resolved_path == "file.py"
        assert result.resolution_method == "extension_change"
    
    def test_change_extension_remove(self):
        """拡張子削除のテスト"""
        result = change_extension_pure("file.txt", "")
        
        assert result.resolved_path == "file"
        assert result.resolution_method == "extension_change"
    
    def test_change_extension_no_original(self):
        """元の拡張子なしファイルの拡張子変更テスト"""
        result = change_extension_pure("file", ".txt")
        
        assert result.resolved_path == "file.txt"


class TestAnalyzePathStructure:
    """パス構造分析のテスト"""
    
    def test_analyze_simple_path(self):
        """シンプルなパス分析のテスト"""
        analysis = analyze_path_structure_pure("dir/file.txt")
        
        assert analysis["original_path"] == "dir/file.txt"
        assert analysis["name"] == "file.txt"
        assert analysis["stem"] == "file"
        assert analysis["suffix"] == ".txt"
        assert analysis["has_extension"] is True
        assert analysis["is_hidden"] is False
        assert analysis["part_count"] == 2
    
    def test_analyze_absolute_path(self):
        """絶対パス分析のテスト"""
        analysis = analyze_path_structure_pure("/home/user/file.txt")
        
        assert analysis["is_absolute"] is True
        assert analysis["name"] == "file.txt"
        assert analysis["depth"] >= 2
    
    def test_analyze_hidden_file(self):
        """隠しファイル分析のテスト"""
        analysis = analyze_path_structure_pure(".hidden_file")
        
        assert analysis["is_hidden"] is True
        assert analysis["name"] == ".hidden_file"
    
    def test_analyze_multiple_extensions(self):
        """複数拡張子分析のテスト"""
        analysis = analyze_path_structure_pure("archive.tar.gz")
        
        assert analysis["suffix"] == ".gz"
        assert analysis["suffixes"] == [".tar", ".gz"]
        assert analysis["has_extension"] is True
    
    def test_analyze_no_extension(self):
        """拡張子なしファイル分析のテスト"""
        analysis = analyze_path_structure_pure("no_extension_file")
        
        assert analysis["has_extension"] is False
        assert analysis["suffix"] == ""


class TestFindCommonParent:
    """共通親ディレクトリ検索のテスト"""
    
    def test_find_common_parent_simple(self):
        """シンプルな共通親検索のテスト"""
        paths = ["/base/dir1/file1", "/base/dir2/file2", "/base/dir3/file3"]
        
        common = find_common_parent_pure(paths)
        
        assert common == "/base"
    
    def test_find_common_parent_no_common(self):
        """共通親なしの検索テスト"""
        paths = ["/path1/file", "/different/file"]
        
        common = find_common_parent_pure(paths)
        
        # ルートが共通親になる場合またはNone
        assert common is None or common == "/"
    
    def test_find_common_parent_single_path(self):
        """単一パスの共通親検索テスト"""
        paths = ["/home/user/file.txt"]
        
        common = find_common_parent_pure(paths)
        
        assert common == "/home/user"
    
    def test_find_common_parent_empty_list(self):
        """空リストの共通親検索テスト"""
        common = find_common_parent_pure([])
        
        assert common is None
    
    def test_find_common_parent_relative_paths(self):
        """相対パスの共通親検索テスト"""
        paths = ["dir1/file1", "dir1/file2", "dir1/subdir/file3"]
        
        common = find_common_parent_pure(paths)
        
        assert "dir1" in common


class TestValidatePathSecurity:
    """パスセキュリティ検証のテスト"""
    
    def test_validate_secure_path(self):
        """安全なパスの検証テスト"""
        result = validate_path_security_pure("safe/path/file.txt")
        
        assert result["is_secure"] is True
        assert len(result["security_issues"]) == 0
        assert result["risk_level"] == "none"
    
    def test_validate_traversal_attack(self):
        """トラバーサル攻撃の検証テスト"""
        result = validate_path_security_pure("../../../etc/passwd")
        
        assert result["is_secure"] is False
        assert len(result["security_issues"]) >= 1
        assert any("traversal" in issue for issue in result["security_issues"])
        assert result["risk_level"] == "high"
    
    def test_validate_absolute_path_warning(self):
        """絶対パス警告の検証テスト"""
        result = validate_path_security_pure("/absolute/path")
        
        assert result["is_secure"] is True  # 警告のみ
        assert len(result["warnings"]) >= 1
        assert any("absolute" in warning for warning in result["warnings"])
        assert result["risk_level"] == "low"
    
    def test_validate_hidden_files(self):
        """隠しファイル警告の検証テスト"""
        result = validate_path_security_pure("path/.hidden/file")
        
        assert len(result["warnings"]) >= 1
        assert any("hidden" in warning for warning in result["warnings"])
    
    def test_validate_suspicious_characters(self):
        """怪しい文字の検証テスト"""
        result = validate_path_security_pure("file<>name")
        
        assert result["is_secure"] is False
        assert any("suspicious" in issue for issue in result["security_issues"])
        assert result["risk_level"] == "high"


class TestGeneratePathVariations:
    """パスバリエーション生成のテスト"""
    
    def test_generate_basic_variations(self):
        """基本バリエーション生成のテスト"""
        variations = generate_path_variations_pure(
            "/base/file.txt", 
            ["parent", "without_extension", "name_only"]
        )
        
        assert variations["parent"] == "/base"
        assert variations["without_extension"] == "/base/file"
        assert variations["name_only"] == "file.txt"
    
    def test_generate_custom_variations(self):
        """カスタムバリエーション生成のテスト"""
        variations = generate_path_variations_pure(
            "file.txt",
            ["backup", "temp"]
        )
        
        assert variations["backup"] == "file.backup"
        assert variations["temp"] == "file.temp"
    
    def test_generate_absolute_variation(self):
        """絶対パスバリエーション生成のテスト"""
        variations = generate_path_variations_pure(
            "relative/file.txt",
            ["absolute"]
        )
        
        # 絶対パスが生成される
        assert Path(variations["absolute"]).is_absolute()
    
    def test_generate_stem_variation(self):
        """ステムバリエーション生成のテスト"""
        variations = generate_path_variations_pure(
            "path/file.txt",
            ["stem_only"]
        )
        
        assert variations["stem_only"] == "file"


class TestCalculatePathMetrics:
    """パスメトリクス計算のテスト"""
    
    def test_calculate_metrics_mixed_paths(self):
        """混合パスのメトリクス計算テスト"""
        paths = [
            "/absolute/path/file.txt",
            "relative/path/file.py",
            "another/file.txt",
            "single_file.js"
        ]
        
        metrics = calculate_path_metrics_pure(paths)
        
        assert metrics["total_paths"] == 4
        assert metrics["absolute_paths"] == 1
        assert metrics["relative_paths"] == 3
        assert metrics["avg_depth"] > 0
        assert metrics["extensions"][".txt"] == 2
        assert metrics["extensions"][".py"] == 1
        assert metrics["extensions"][".js"] == 1
    
    def test_calculate_metrics_empty_list(self):
        """空リストのメトリクス計算テスト"""
        metrics = calculate_path_metrics_pure([])
        
        assert metrics["total_paths"] == 0
        assert metrics["absolute_paths"] == 0
        assert metrics["relative_paths"] == 0
        assert metrics["avg_depth"] == 0
        assert metrics["extensions"] == {}
    
    def test_calculate_metrics_same_extensions(self):
        """同じ拡張子のメトリクス計算テスト"""
        paths = ["file1.py", "file2.py", "file3.py"]
        
        metrics = calculate_path_metrics_pure(paths)
        
        assert metrics["extensions"][".py"] == 3
        assert len(metrics["extensions"]) == 1
    
    def test_calculate_metrics_depths(self):
        """深度メトリクス計算テスト"""
        paths = [
            "shallow.txt",
            "medium/depth/file.txt",
            "very/deep/nested/directory/file.txt"
        ]
        
        metrics = calculate_path_metrics_pure(paths)
        
        assert metrics["min_depth"] == 1
        assert metrics["max_depth"] == 5
        assert 1 < metrics["avg_depth"] < 5


class TestComplexScenarios:
    """複雑なシナリオのテスト"""
    
    def test_complete_path_processing_workflow(self):
        """完全なパス処理ワークフローのテスト"""
        # 1. パス分析
        original_path = "project/../src/./file.txt"
        analysis = analyze_path_structure_pure(original_path)
        
        # 2. セキュリティ検証
        security = validate_path_security_pure(original_path)
        
        # 3. 正規化
        normalized = normalize_path_pure(original_path)
        
        # 4. バリエーション生成
        variations = generate_path_variations_pure(
            normalized.resolved_path,
            ["parent", "without_extension", "backup"]
        )
        
        # 5. 安全なパス結合
        safe_result = safe_path_join_pure("base", "safe", "path")
        
        # 結果検証
        assert analysis["original_path"] == original_path
        assert not security["is_secure"]  # .. が含まれているため
        assert normalized.resolution_method == "normalize"
        assert len(variations) == 3
        assert safe_result.is_safe is True
    
    def test_batch_path_analysis(self):
        """バッチパス分析のテスト"""
        paths = [
            "/absolute/secure/file.txt",
            "relative/path/file.py",
            "../dangerous/traversal.txt",
            "normal/file.js",
            "/home/.hidden/secret.txt"
        ]
        
        # 各パスを分析
        analyses = [analyze_path_structure_pure(p) for p in paths]
        security_checks = [validate_path_security_pure(p) for p in paths]
        
        # 全体メトリクス
        metrics = calculate_path_metrics_pure(paths)
        
        # 結果検証
        assert len(analyses) == 5
        assert len(security_checks) == 5
        
        # セキュリティ問題のあるパスが検出される
        insecure_count = sum(1 for s in security_checks if not s["is_secure"])
        assert insecure_count >= 1  # .. を含むパスがある
        
        # メトリクスが正しく計算される
        assert metrics["total_paths"] == 5
        assert metrics["absolute_paths"] >= 2
    
    def test_error_resilience(self):
        """エラー耐性のテスト"""
        # 様々な問題のあるパスでテスト
        problematic_paths = [
            "",           # 空文字列
            None,         # None（文字列変換される）
            "a" * 1000,   # 非常に長いパス
        ]
        
        for path in problematic_paths:
            try:
                # すべての関数がエラーを適切に処理することを確認
                analysis = analyze_path_structure_pure(str(path) if path is not None else "")
                security = validate_path_security_pure(str(path) if path is not None else "")
                
                # 結果が返されることを確認（エラーで停止しない）
                assert "original_path" in analysis
                assert "is_secure" in security
            except Exception as e:
                pytest.fail(f"Function should handle problematic path gracefully: {e}")