"""
Comprehensive tests for template processor module
"""
import pytest
from src.pure_functions.formatting.core.template_processor import (
    build_path_template,
    validate_template_keys,
    TemplateValidator
)


class TestBuildPathTemplate:
    """Test build_path_template function"""
    
    def test_basic_path_building(self):
        """Test basic path template building"""
        result = build_path_template("/base", "sub", "file.py")
        assert result == "/base/sub/file.py"
    
    def test_trailing_slashes_removed(self):
        """Test that trailing slashes are handled correctly"""
        result = build_path_template("/base/", "sub/", "file.py")
        assert result == "/base/sub/file.py"
    
    def test_leading_slashes_removed_from_parts(self):
        """Test that leading slashes in parts are removed"""
        result = build_path_template("/base", "/sub", "/file.py")
        assert result == "/base/sub/file.py"
    
    def test_empty_parts(self):
        """Test with empty parts"""
        result = build_path_template("/base", "", "file.py")
        assert result == "/base//file.py"  # Empty parts create double slashes
    
    def test_single_part(self):
        """Test with only base path"""
        result = build_path_template("/base")
        assert result == "/base"
    
    def test_relative_base_path(self):
        """Test with relative base path"""
        result = build_path_template("base", "sub", "file.py")
        assert result == "base/sub/file.py"
    
    def test_with_template_variables(self):
        """Test building path with template variables"""
        result = build_path_template("/base", "{dir}", "{filename}.py")
        assert result == "/base/{dir}/{filename}.py"
    
    def test_multiple_slashes(self):
        """Test handling of multiple slashes"""
        result = build_path_template("/base///", "///sub///", "//file.py")
        assert result == "/base/sub/file.py"
    
    def test_windows_style_paths(self):
        """Test that forward slashes are used even with backslashes"""
        # This maintains Unix-style paths
        result = build_path_template("C:\\base", "sub", "file.py")
        assert result == "C:\\base/sub/file.py"


class TestValidateTemplateKeys:
    """Test validate_template_keys function"""
    
    def test_all_keys_present(self):
        """Test when all required keys are present"""
        template = "/{foo}/{bar}/{baz}"
        required = ["foo", "bar", "baz"]
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is True
        assert missing == []
    
    def test_missing_keys(self):
        """Test when some keys are missing"""
        template = "/{foo}/{bar}"
        required = ["foo", "bar", "baz"]
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is False
        assert missing == ["baz"]
    
    def test_extra_keys_allowed(self):
        """Test that extra keys in template are allowed"""
        template = "/{foo}/{bar}/{baz}/{extra}"
        required = ["foo", "bar"]
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is True
        assert missing == []
    
    def test_no_required_keys(self):
        """Test with no required keys"""
        template = "/{foo}/{bar}"
        required = []
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is True
        assert missing == []
    
    def test_no_keys_in_template(self):
        """Test template with no keys"""
        template = "/static/path/file.py"
        required = ["foo"]
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is False
        assert missing == ["foo"]
    
    def test_duplicate_keys_in_template(self):
        """Test template with duplicate keys"""
        template = "/{foo}/middle/{foo}/end"
        required = ["foo"]
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is True
        assert missing == []
    
    def test_case_sensitivity(self):
        """Test that key matching is case sensitive"""
        template = "/{Foo}/{BAR}"
        required = ["foo", "bar"]
        is_valid, missing = validate_template_keys(template, required)
        assert is_valid is False
        assert missing == ["foo", "bar"]


class TestTemplateValidator:
    """Test TemplateValidator class"""
    
    def test_basic_initialization(self):
        """Test basic TemplateValidator initialization"""
        validator = TemplateValidator()
        assert validator.required_keys == []
        
        validator = TemplateValidator(["foo", "bar"])
        assert validator.required_keys == ["foo", "bar"]
    
    def test_validate_with_class_required_keys(self):
        """Test validation using class-level required keys"""
        validator = TemplateValidator(["base", "env"])
        
        # Valid template
        is_valid, missing = validator.validate("/{base}/{env}/file.py")
        assert is_valid is True
        assert missing == []
        
        # Missing keys
        is_valid, missing = validator.validate("/{base}/file.py")
        assert is_valid is False
        assert missing == ["env"]
    
    def test_validate_with_additional_keys(self):
        """Test validation with additional required keys"""
        validator = TemplateValidator(["base"])
        
        # Add additional requirements
        is_valid, missing = validator.validate(
            "/{base}/{extra}/file.py",
            additional_required_keys=["extra", "type"]
        )
        assert is_valid is False
        assert missing == ["type"]
    
    def test_validate_multiple_templates(self):
        """Test validating multiple templates at once"""
        validator = TemplateValidator(["env", "name"])
        
        templates = [
            "/{env}/{name}/main.py",
            "/{env}/config.json",
            "/static/{name}/index.html",
            "/complete/path.txt"
        ]
        
        results = validator.validate_multiple(templates)
        
        assert len(results) == 4
        
        # First template - valid
        assert results[0] == ("/{env}/{name}/main.py", True, [])
        
        # Second template - missing 'name'
        assert results[1] == ("/{env}/config.json", False, ["name"])
        
        # Third template - missing 'env'
        assert results[2] == ("/static/{name}/index.html", False, ["env"])
        
        # Fourth template - missing both
        assert results[3] == ("/complete/path.txt", False, ["env", "name"])
    
    def test_get_template_keys(self):
        """Test extracting keys from a template"""
        validator = TemplateValidator()
        
        keys = validator.get_template_keys("/{foo}/{bar}/{baz}")
        assert keys == ["foo", "bar", "baz"]
        
        keys = validator.get_template_keys("/static/path.txt")
        assert keys == []
    
    def test_validate_empty_template(self):
        """Test validating empty template"""
        validator = TemplateValidator(["required"])
        
        is_valid, missing = validator.validate("")
        assert is_valid is False
        assert missing == ["required"]
    
    def test_required_keys_not_modified(self):
        """Test that required_keys list is not modified during validation"""
        original_keys = ["foo", "bar"]
        validator = TemplateValidator(original_keys)
        
        # Validate with additional keys
        validator.validate("/{foo}/{bar}/{baz}", additional_required_keys=["baz"])
        
        # Original list should not be modified
        assert validator.required_keys == ["foo", "bar"]
        assert original_keys == ["foo", "bar"]


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_docker_path_template_validation(self):
        """Test Docker path template validation scenario"""
        # Docker paths often need these keys
        validator = TemplateValidator(["container", "mount_path"])
        
        docker_template = "/{container}:{mount_path}/{workspace}"
        is_valid, missing = validator.validate(docker_template)
        assert is_valid is True
        assert missing == []
    
    def test_contest_path_template_building(self):
        """Test contest path template building scenario"""
        # Build a complex contest path template
        template = build_path_template(
            "/contest_root",
            "{contest_name}",
            "{problem_id}",
            "{language}",
            "main.{extension}"
        )
        
        expected = "/contest_root/{contest_name}/{problem_id}/{language}/main.{extension}"
        assert template == expected
        
        # Validate it has required keys
        validator = TemplateValidator(["contest_name", "problem_id"])
        is_valid, missing = validator.validate(template)
        assert is_valid is True
        assert missing == []
    
    def test_multi_environment_templates(self):
        """Test validating templates for multiple environments"""
        validator = TemplateValidator(["env", "project"])
        
        env_templates = {
            "docker": "/docker/{env}/{project}/app",
            "local": "/local/{project}/env/{env}",
            "cloud": "/cloud/{env}/{region}/{project}"  # Has extra 'region' key
        }
        
        for env_name, template in env_templates.items():
            is_valid, missing = validator.validate(template)
            assert is_valid is True, f"Template for {env_name} should be valid"
            assert missing == []