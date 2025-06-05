"""
Comprehensive tests for path formatter module
"""
import pytest
from src.pure_functions.formatting.specialized.path_formatter import (
    build_context_path,
    format_path_template,
    validate_path_template,
    normalize_path_separators,
    join_path_parts,
    PathFormatter
)


class TestBuildContextPath:
    """Test build_context_path function"""
    
    def test_basic_context_path_building(self):
        """Test basic context path building"""
        context = {'lang': 'python', 'contest': 'abc123'}
        template = '/base/{lang}/{contest}'
        
        result = build_context_path(template, context)
        assert result == '/base/python/abc123'
    
    def test_context_path_with_additional_parts(self):
        """Test context path building with additional parts"""
        context = {'lang': 'python', 'contest': 'abc123'}
        template = '/base/{lang}/{contest}'
        
        result = build_context_path(template, context, 'problem_a', 'main.py')
        assert result == '/base/python/abc123/problem_a/main.py'
    
    def test_context_path_with_missing_context(self):
        """Test context path building with missing context keys"""
        context = {'lang': 'python'}
        template = '/base/{lang}/{contest}'
        
        result = build_context_path(template, context)
        assert result == '/base/python/{contest}'
    
    def test_context_path_no_additional_parts(self):
        """Test context path building without additional parts"""
        context = {'env': 'docker', 'project': 'myproject'}
        template = '/{env}/{project}/workspace'
        
        result = build_context_path(template, context)
        assert result == '/docker/myproject/workspace'
    
    def test_context_path_empty_template(self):
        """Test context path building with empty template"""
        context = {'key': 'value'}
        template = ''
        
        result = build_context_path(template, context, 'extra')
        assert result == '/extra'
    
    def test_context_path_no_template_keys(self):
        """Test context path building with template having no keys"""
        context = {'unused': 'value'}
        template = '/static/path'
        
        result = build_context_path(template, context, 'additional')
        assert result == '/static/path/additional'


class TestFormatPathTemplate:
    """Test format_path_template function"""
    
    def test_basic_path_template_formatting(self):
        """Test basic path template formatting"""
        template = '/projects/{project_name}/src/{language}'
        context = {'project_name': 'myapp', 'language': 'python'}
        
        result = format_path_template(template, context)
        assert result == '/projects/myapp/src/python'
    
    def test_path_template_with_missing_keys(self):
        """Test path template formatting with missing keys"""
        template = '/projects/{project_name}/src/{language}'
        context = {'project_name': 'myapp'}
        
        result = format_path_template(template, context)
        assert result == '/projects/myapp/src/{language}'
    
    def test_path_template_no_keys(self):
        """Test path template formatting with no template keys"""
        template = '/static/absolute/path'
        context = {'unused': 'value'}
        
        result = format_path_template(template, context)
        assert result == '/static/absolute/path'
    
    def test_path_template_empty_context(self):
        """Test path template formatting with empty context"""
        template = '/base/{key1}/{key2}'
        context = {}
        
        result = format_path_template(template, context)
        assert result == '/base/{key1}/{key2}'


class TestValidatePathTemplate:
    """Test validate_path_template function"""
    
    def test_valid_path_template(self):
        """Test validation of valid path template"""
        template = '/base/{project}/{env}'
        required_keys = ['project', 'env']
        
        is_valid, missing = validate_path_template(template, required_keys)
        assert is_valid is True
        assert missing == []
    
    def test_invalid_path_template_missing_keys(self):
        """Test validation of path template with missing keys"""
        template = '/base/{project}'
        required_keys = ['project', 'env', 'language']
        
        is_valid, missing = validate_path_template(template, required_keys)
        assert is_valid is False
        assert missing == ['env', 'language']
    
    def test_path_template_extra_keys_allowed(self):
        """Test that extra keys in template are allowed"""
        template = '/base/{project}/{env}/{extra}/{another}'
        required_keys = ['project', 'env']
        
        is_valid, missing = validate_path_template(template, required_keys)
        assert is_valid is True
        assert missing == []
    
    def test_path_template_no_required_keys(self):
        """Test validation with no required keys"""
        template = '/any/{template}/format'
        required_keys = []
        
        is_valid, missing = validate_path_template(template, required_keys)
        assert is_valid is True
        assert missing == []


class TestNormalizePathSeparators:
    """Test normalize_path_separators function"""
    
    def test_normalize_backslashes_to_forward(self):
        """Test normalizing backslashes to forward slashes"""
        path = 'C:\\Users\\name\\Documents'
        result = normalize_path_separators(path)
        assert result == 'C:/Users/name/Documents'
    
    def test_normalize_mixed_separators(self):
        """Test normalizing mixed path separators"""
        path = '/home\\user/Documents\\file.txt'
        result = normalize_path_separators(path)
        assert result == '/home/user/Documents/file.txt'
    
    def test_normalize_double_slashes(self):
        """Test normalizing double slashes"""
        path = '/home//user//Documents///file.txt'
        result = normalize_path_separators(path)
        assert result == '/home/user/Documents/file.txt'
    
    def test_normalize_to_backslashes(self):
        """Test normalizing to backslashes"""
        path = '/home/user/Documents'
        result = normalize_path_separators(path, target_separator='\\')
        assert result == '\\home\\user\\Documents'
    
    def test_normalize_already_normalized(self):
        """Test normalizing already normalized path"""
        path = '/home/user/Documents/file.txt'
        result = normalize_path_separators(path)
        assert result == '/home/user/Documents/file.txt'
    
    def test_normalize_empty_path(self):
        """Test normalizing empty path"""
        path = ''
        result = normalize_path_separators(path)
        assert result == ''
    
    def test_normalize_complex_multiple_separators(self):
        """Test normalizing complex path with multiple consecutive separators"""
        path = '//home///user\\\\Documents///'
        result = normalize_path_separators(path)
        assert result == '/home/user/Documents/'


class TestJoinPathParts:
    """Test join_path_parts function"""
    
    def test_basic_path_joining(self):
        """Test basic path part joining"""
        result = join_path_parts('home', 'user', 'Documents')
        assert result == 'home/user/Documents'
    
    def test_path_joining_with_custom_separator(self):
        """Test path joining with custom separator"""
        result = join_path_parts('home', 'user', 'Documents', separator='\\')
        assert result == 'home\\user\\Documents'
    
    def test_path_joining_with_leading_trailing_separators(self):
        """Test path joining with leading/trailing separators in parts"""
        result = join_path_parts('/home/', '/user/', '/Documents/')
        assert result == 'home/user/Documents'
    
    def test_path_joining_with_empty_parts(self):
        """Test path joining with empty parts"""
        result = join_path_parts('home', '', 'user', '', 'Documents')
        assert result == 'home/user/Documents'
    
    def test_path_joining_all_empty_parts(self):
        """Test path joining with all empty parts"""
        result = join_path_parts('', '', '')
        assert result == ''
    
    def test_path_joining_no_parts(self):
        """Test path joining with no parts"""
        result = join_path_parts()
        assert result == ''
    
    def test_path_joining_single_part(self):
        """Test path joining with single part"""
        result = join_path_parts('onlypart')
        assert result == 'onlypart'
    
    def test_path_joining_with_whitespace_only_parts(self):
        """Test path joining with whitespace-only parts"""
        result = join_path_parts('home', '   ', 'Documents')
        assert result == 'home/Documents'


class TestPathFormatter:
    """Test PathFormatter class"""
    
    def test_path_formatter_initialization_defaults(self):
        """Test PathFormatter initialization with defaults"""
        formatter = PathFormatter()
        
        assert formatter.base_paths == {}
        assert formatter.default_context == {}
        assert formatter.path_separator == '/'
    
    def test_path_formatter_initialization_custom(self):
        """Test PathFormatter initialization with custom values"""
        base_paths = {'project': '/projects/{name}'}
        default_context = {'env': 'development'}
        
        formatter = PathFormatter(
            base_paths=base_paths,
            default_context=default_context,
            path_separator='\\'
        )
        
        assert formatter.base_paths == base_paths
        assert formatter.default_context == default_context
        assert formatter.path_separator == '\\'
    
    def test_format_path_basic(self):
        """Test basic path formatting"""
        base_paths = {
            'project_root': '/projects/{project_name}',
            'source_dir': '/projects/{project_name}/src/{language}'
        }
        formatter = PathFormatter(base_paths=base_paths)
        
        context = {'project_name': 'myapp', 'language': 'python'}
        result = formatter.format_path('source_dir', context)
        
        assert result == '/projects/myapp/src/python'
    
    def test_format_path_with_default_context(self):
        """Test path formatting with default context"""
        base_paths = {'workspace': '/workspace/{env}/{project}'}
        default_context = {'env': 'docker'}
        
        formatter = PathFormatter(
            base_paths=base_paths,
            default_context=default_context
        )
        
        result = formatter.format_path('workspace', {'project': 'myapp'})
        assert result == '/workspace/docker/myapp'
    
    def test_format_path_context_override(self):
        """Test path formatting with context overriding defaults"""
        base_paths = {'app': '/apps/{env}/{name}'}
        default_context = {'env': 'development', 'name': 'default'}
        
        formatter = PathFormatter(
            base_paths=base_paths,
            default_context=default_context
        )
        
        # Override default values
        result = formatter.format_path('app', {'env': 'production', 'name': 'myapp'})
        assert result == '/apps/production/myapp'
    
    def test_format_path_with_additional_parts(self):
        """Test path formatting with additional parts"""
        base_paths = {'base': '/base/{project}'}
        formatter = PathFormatter(base_paths=base_paths)
        
        result = formatter.format_path('base', {'project': 'myapp'}, 'src', 'main.py')
        assert result == '/base/myapp/src/main.py'
    
    def test_format_path_unknown_key(self):
        """Test path formatting with unknown key"""
        formatter = PathFormatter()
        
        with pytest.raises(ValueError, match="Unknown path key: unknown"):
            formatter.format_path('unknown', {})
    
    def test_add_base_path(self):
        """Test adding base path template"""
        formatter = PathFormatter()
        
        formatter.add_base_path('new_path', '/new/{template}')
        assert 'new_path' in formatter.base_paths
        assert formatter.base_paths['new_path'] == '/new/{template}'
    
    def test_update_default_context(self):
        """Test updating default context"""
        formatter = PathFormatter(default_context={'env': 'dev'})
        
        formatter.update_default_context({'project': 'myapp', 'env': 'prod'})
        
        assert formatter.default_context['project'] == 'myapp'
        assert formatter.default_context['env'] == 'prod'  # Should be updated
    
    def test_validate_all_paths(self):
        """Test validating all base paths"""
        base_paths = {
            'valid': '/base/{project}/{env}',
            'invalid': '/base/{project}',
            'another_valid': '/other/{project}/{env}/{extra}'
        }
        formatter = PathFormatter(base_paths=base_paths)
        
        required_keys = ['project', 'env']
        results = formatter.validate_all_paths(required_keys)
        
        assert results['valid'] == (True, [])
        assert results['invalid'] == (False, ['env'])
        assert results['another_valid'] == (True, [])
    
    def test_get_path_keys(self):
        """Test getting keys from path template"""
        base_paths = {
            'complex': '/base/{project}/{env}/{language}/src'
        }
        formatter = PathFormatter(base_paths=base_paths)
        
        keys = formatter.get_path_keys('complex')
        assert keys == ['project', 'env', 'language']
    
    def test_get_path_keys_unknown_path(self):
        """Test getting keys from unknown path"""
        formatter = PathFormatter()
        
        keys = formatter.get_path_keys('unknown')
        assert keys == []
    
    def test_get_path_keys_no_template_keys(self):
        """Test getting keys from path with no template keys"""
        base_paths = {'static': '/static/absolute/path'}
        formatter = PathFormatter(base_paths=base_paths)
        
        keys = formatter.get_path_keys('static')
        assert keys == []


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_contest_programming_paths(self):
        """Test contest programming project path structure"""
        base_paths = {
            'contest_dir': '/contests/{contest_name}',
            'problem_dir': '/contests/{contest_name}/{problem_id}',
            'solution_file': '/contests/{contest_name}/{problem_id}/{language}/main.{ext}'
        }
        
        default_context = {
            'language': 'python',
            'ext': 'py'
        }
        
        formatter = PathFormatter(
            base_paths=base_paths,
            default_context=default_context
        )
        
        context = {'contest_name': 'abc123', 'problem_id': 'a'}
        
        # Test different path generations
        contest_path = formatter.format_path('contest_dir', context)
        assert contest_path == '/contests/abc123'
        
        problem_path = formatter.format_path('problem_dir', context)
        assert contest_path == '/contests/abc123'
        
        solution_path = formatter.format_path('solution_file', context)
        assert solution_path == '/contests/abc123/a/python/main.py'
        
        # Test with language override
        cpp_solution = formatter.format_path('solution_file', {
            **context,
            'language': 'cpp',
            'ext': 'cpp'
        })
        assert cpp_solution == '/contests/abc123/a/cpp/main.cpp'
    
    def test_docker_environment_paths(self):
        """Test Docker environment path structure"""
        base_paths = {
            'container_workspace': '/workspace/{project}',
            'host_mount': '/host/projects/{project}',
            'dockerfile_path': '/docker/{env}/{project}/Dockerfile'
        }
        
        formatter = PathFormatter(base_paths=base_paths)
        
        context = {'project': 'myapp', 'env': 'development'}
        
        # Test path generation
        workspace = formatter.format_path('container_workspace', context)
        assert workspace == '/workspace/myapp'
        
        mount = formatter.format_path('host_mount', context)
        assert mount == '/host/projects/myapp'
        
        dockerfile = formatter.format_path('dockerfile_path', context)
        assert dockerfile == '/docker/development/myapp/Dockerfile'
        
        # Test with additional parts
        source_file = formatter.format_path('container_workspace', context, 'src', 'main.py')
        assert source_file == '/workspace/myapp/src/main.py'
    
    def test_cross_platform_path_handling(self):
        """Test cross-platform path handling"""
        # Simulate Windows-style base paths
        base_paths = {
            'windows_style': 'C:\\Projects\\{name}\\src',
            'mixed_style': '/unix/path\\{name}//subdir'
        }
        
        formatter = PathFormatter(base_paths=base_paths)
        
        context = {'name': 'myproject'}
        
        # Format paths and normalize
        windows_path = formatter.format_path('windows_style', context)
        mixed_path = formatter.format_path('mixed_style', context)
        
        # Normalize separators
        normalized_windows = normalize_path_separators(windows_path)
        normalized_mixed = normalize_path_separators(mixed_path)
        
        assert normalized_windows == 'C:/Projects/myproject/src'
        assert normalized_mixed == '/unix/path/myproject/subdir'