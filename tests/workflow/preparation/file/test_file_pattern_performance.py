"""Performance tests for FilePatternService functionality."""
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock
import pytest

from src.workflow.preparation.file.file_pattern_service import FilePatternService
from src.infrastructure.config.json_config_loader import JsonConfigLoader
from src.domain.interfaces.filesystem_interface import FileSystemInterface
from src.domain.interfaces.logger_interface import LoggerInterface


class TestFilePatternPerformance:
    """Performance tests for FilePatternService."""

    @pytest.fixture
    def temp_workspace_large(self):
        """Create temporary workspace with many test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            
            # Create test directory structure with many files
            test_dir = workspace / "test"
            test_dir.mkdir()
            
            # Create 100 test files of various types
            for i in range(100):
                (test_dir / f"sample{i:03d}.txt").write_text(f"test data {i}")
                (test_dir / f"input{i:03d}.in").write_text(f"input data {i}")
                (test_dir / f"output{i:03d}.out").write_text(f"output data {i}")
            
            # Create nested structure
            for subdir_idx in range(10):
                subdir = test_dir / f"subdir_{subdir_idx}"
                subdir.mkdir()
                for file_idx in range(10):
                    (subdir / f"nested_{file_idx}.txt").write_text(f"nested {subdir_idx}-{file_idx}")
            
            # Create source files
            for i in range(50):
                (workspace / f"source{i:03d}.cpp").write_text(f"// Source file {i}")
                (workspace / f"header{i:03d}.h").write_text(f"// Header file {i}")
            
            yield workspace

    @pytest.fixture
    def mock_config_loader_perf(self):
        """Mock JsonConfigLoader for performance testing."""
        mock = Mock(spec=JsonConfigLoader)
        mock.get_language_config.return_value = {
            "file_patterns": {
                "test_files": {
                    "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                    "contest_current": ["test/"],
                    "contest_stock": ["test/"]
                },
                "contest_files": {
                    "workspace": ["*.cpp", "*.h", "*.hpp"],
                    "contest_current": ["main.cpp"],
                    "contest_stock": ["*.cpp", "*.h", "*.hpp"]
                }
            }
        }
        mock.get_shared_config.return_value = {
            "file_operations": {
                "move_test_files": [
                    ["workspace.test_files", "contest_current.test_files"],
                    ["workspace.contest_files", "contest_stock.contest_files"]
                ]
            }
        }
        return mock

    @pytest.fixture
    def mock_file_driver_perf(self):
        """Mock FileDriver for performance testing."""
        mock = Mock(spec=FileSystemInterface)
        mock.copy_file.return_value = True
        mock.create_directory.return_value = True
        return mock

    @pytest.fixture
    def mock_logger_perf(self):
        """Mock Logger for performance testing."""
        return Mock(spec=LoggerInterface)

    @pytest.fixture
    def service_perf(self, mock_config_loader_perf, mock_file_driver_perf, mock_logger_perf):
        """Create FilePatternService for performance testing."""
        return FilePatternService(mock_config_loader_perf, mock_file_driver_perf, mock_logger_perf)

    def test_pattern_resolution_performance(self, service_perf, temp_workspace_large):
        """Test pattern resolution performance with many files."""
        context = {
            "workspace_path": str(temp_workspace_large),
            "language": "cpp"
        }
        
        # Measure pattern resolution time
        start_time = time.time()
        
        # Resolve test files pattern (should find 1000+ files)
        test_files = service_perf.resolve_pattern_paths("workspace.test_files", context)
        
        # Resolve source files pattern (should find 100+ files)
        source_files = service_perf.resolve_pattern_paths("workspace.contest_files", context)
        
        end_time = time.time()
        resolution_time = end_time - start_time
        
        # Performance assertions
        assert len(test_files) >= 1000  # 300 direct + 100 nested files
        assert len(source_files) >= 100  # 50 cpp + 50 h files
        assert resolution_time < 2.0  # Should complete within 2 seconds
        
        print(f"Pattern resolution completed in {resolution_time:.3f}s")
        print(f"Found {len(test_files)} test files and {len(source_files)} source files")

    def test_file_operations_performance(self, service_perf, temp_workspace_large):
        """Test file operations performance with many files."""
        context = {
            "workspace_path": str(temp_workspace_large),
            "contest_current_path": str(temp_workspace_large / "contest_current"),
            "contest_stock_path": str(temp_workspace_large / "contest_stock"),
            "language": "cpp"
        }
        
        # Create destination directories
        (temp_workspace_large / "contest_current").mkdir()
        (temp_workspace_large / "contest_stock").mkdir()
        
        # Measure file operations time
        start_time = time.time()
        
        result = service_perf.execute_file_operations("move_test_files", context)
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Performance assertions
        assert result.success is True
        assert result.files_processed >= 1000  # Should process many files
        assert operation_time < 5.0  # Should complete within 5 seconds
        
        print(f"File operations completed in {operation_time:.3f}s")
        print(f"Processed {result.files_processed} files")

    def test_validation_performance(self, service_perf):
        """Test configuration validation performance."""
        # Create large configuration for testing
        large_patterns = {}
        for i in range(50):  # 50 pattern groups
            large_patterns[f"group_{i}"] = {
                "workspace": [f"pattern_{j}/**/*" for j in range(20)],  # 20 patterns each
                "contest_current": [f"current_{j}/"],
                "contest_stock": [f"stock_{j}/"]
            }
        
        large_operations = {}
        for i in range(20):  # 20 operations
            large_operations[f"operation_{i}"] = [
                [f"workspace.group_{j}", f"contest_current.group_{j}"] 
                for j in range(10)  # 10 steps each
            ]
        
        # Measure validation time
        start_time = time.time()
        
        patterns_valid, pattern_errors = service_perf.validate_patterns(large_patterns)
        operations_valid, operation_errors = service_perf.validate_operations(large_operations)
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # Performance assertions
        assert patterns_valid is True
        assert operations_valid is True
        assert validation_time < 1.0  # Should complete within 1 second
        
        print(f"Validation completed in {validation_time:.3f}s")
        print(f"Validated {len(large_patterns)} pattern groups and {len(large_operations)} operations")

    def test_diagnosis_performance(self, service_perf, mock_config_loader_perf):
        """Test configuration diagnosis performance."""
        # Setup mock to return large configuration
        mock_config_loader_perf.get_language_config.return_value = {
            "file_patterns": {f"group_{i}": {
                "workspace": [f"**/*.{ext}" for ext in ["txt", "in", "out", "cpp", "h"]],
                "contest_current": ["test/"],
                "contest_stock": ["test/"]
            } for i in range(100)}  # 100 pattern groups
        }
        
        # Measure diagnosis time
        start_time = time.time()
        
        diagnosis = service_perf.diagnose_config_issues("cpp")
        
        end_time = time.time()
        diagnosis_time = end_time - start_time
        
        # Performance assertions
        assert diagnosis["config_status"] == "valid"
        assert diagnosis_time < 1.0  # Should complete within 1 second
        
        print(f"Diagnosis completed in {diagnosis_time:.3f}s")

    def test_memory_usage_estimation(self, service_perf, temp_workspace_large):
        """Test memory usage with large file sets."""
        context = {
            "workspace_path": str(temp_workspace_large),
            "language": "cpp"
        }
        
        # Resolve patterns multiple times to test memory management
        total_files = 0
        for _ in range(10):  # 10 iterations
            test_files = service_perf.resolve_pattern_paths("workspace.test_files", context)
            source_files = service_perf.resolve_pattern_paths("workspace.contest_files", context)
            total_files += len(test_files) + len(source_files)
        
        # Memory should not grow excessively
        assert total_files > 10000  # Should have processed many files
        print(f"Processed {total_files} file references across 10 iterations")

    def test_concurrent_pattern_resolution(self, service_perf, temp_workspace_large):
        """Test pattern resolution under concurrent-like conditions."""
        import threading
        
        context = {
            "workspace_path": str(temp_workspace_large),
            "language": "cpp"
        }
        
        results = []
        errors = []
        
        def resolve_patterns():
            try:
                test_files = service_perf.resolve_pattern_paths("workspace.test_files", context)
                results.append(len(test_files))
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to simulate concurrent access
        threads = []
        start_time = time.time()
        
        for _ in range(5):  # 5 concurrent operations
            thread = threading.Thread(target=resolve_patterns)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Performance assertions
        assert len(errors) == 0  # No errors should occur
        assert len(results) == 5  # All threads should complete
        assert all(r >= 1000 for r in results)  # Each should find many files
        assert concurrent_time < 10.0  # Should complete within 10 seconds
        
        print(f"Concurrent pattern resolution completed in {concurrent_time:.3f}s")
        print(f"Results: {results}")


class TestFilePatternBenchmarks:
    """Benchmark tests for FilePatternService."""

    def test_benchmark_pattern_types(self, temp_workspace_large):
        """Benchmark different pattern types."""
        mock_config = Mock(spec=JsonConfigLoader)
        mock_file_driver = Mock(spec=FileSystemInterface)
        mock_logger = Mock(spec=LoggerInterface)
        mock_file_driver.copy_file.return_value = True
        mock_file_driver.create_directory.return_value = True
        
        service = FilePatternService(mock_config, mock_file_driver, mock_logger)
        
        context = {
            "workspace_path": str(temp_workspace_large),
            "language": "cpp"
        }
        
        pattern_types = {
            "simple_wildcard": ["*.txt", "*.cpp"],
            "recursive_wildcard": ["**/*.txt", "**/*.cpp"],
            "complex_patterns": ["test/**/*.{txt,in,out}", "src/**/*.{cpp,h,hpp}"],
            "multiple_directories": ["dir1/**/*", "dir2/**/*", "dir3/**/*"]
        }
        
        benchmark_results = {}
        
        for pattern_name, patterns in pattern_types.items():
            mock_config.get_language_config.return_value = {
                "file_patterns": {
                    "test_group": {
                        "workspace": patterns,
                        "contest_current": ["test/"],
                        "contest_stock": ["test/"]
                    }
                }
            }
            
            start_time = time.time()
            try:
                files = service.resolve_pattern_paths("workspace.test_group", context)
                end_time = time.time()
                benchmark_results[pattern_name] = {
                    "time": end_time - start_time,
                    "files_found": len(files),
                    "success": True
                }
            except Exception as e:
                end_time = time.time()
                benchmark_results[pattern_name] = {
                    "time": end_time - start_time,
                    "files_found": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Print benchmark results
        print("\nPattern Performance Benchmark:")
        print("-" * 50)
        for pattern_name, result in benchmark_results.items():
            if result["success"]:
                print(f"{pattern_name:20}: {result['time']:.3f}s ({result['files_found']} files)")
            else:
                print(f"{pattern_name:20}: {result['time']:.3f}s (FAILED: {result['error']})")
        
        # All patterns should complete reasonably quickly
        for result in benchmark_results.values():
            if result["success"]:
                assert result["time"] < 3.0  # No pattern should take more than 3 seconds

    def test_scalability_benchmark(self):
        """Test scalability with increasing file counts."""
        mock_config = Mock(spec=JsonConfigLoader)
        mock_file_driver = Mock(spec=FileSystemInterface)
        mock_logger = Mock(spec=LoggerInterface)
        
        service = FilePatternService(mock_config, mock_file_driver, mock_logger)
        
        # Test validation scalability with increasing config sizes
        config_sizes = [10, 50, 100, 200]
        benchmark_results = []
        
        for size in config_sizes:
            # Create config of specified size
            patterns = {
                f"group_{i}": {
                    "workspace": [f"pattern_{j}/**/*" for j in range(5)],
                    "contest_current": ["test/"],
                    "contest_stock": ["test/"]
                } for i in range(size)
            }
            
            start_time = time.time()
            is_valid, errors = service.validate_patterns(patterns)
            end_time = time.time()
            
            benchmark_results.append({
                "config_size": size,
                "time": end_time - start_time,
                "valid": is_valid
            })
        
        # Print scalability results
        print("\nScalability Benchmark:")
        print("-" * 40)
        for result in benchmark_results:
            print(f"Config size {result['config_size']:3d}: {result['time']:.3f}s")
        
        # Validate that time doesn't grow exponentially
        times = [r["time"] for r in benchmark_results]
        assert all(t < 2.0 for t in times)  # No config should take more than 2 seconds
        
        # Time should grow roughly linearly, not exponentially
        if len(times) >= 4:
            # Check that the largest config doesn't take more than 10x the smallest
            assert times[-1] < times[0] * 10