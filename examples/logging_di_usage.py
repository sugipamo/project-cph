"""Example usage of src/logging with dependency injection."""

from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.config.di_config import configure_production_dependencies, configure_test_dependencies
from src.logging import OutputManagerInterface, LogLevel, FormatInfo


def production_example():
    """Production usage example."""
    # Setup production DI container
    container = DIContainer()
    configure_production_dependencies(container)
    
    # Resolve logging output manager
    output_manager: OutputManagerInterface = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    
    # Use the output manager
    output_manager.add("アプリケーション開始", LogLevel.INFO)
    output_manager.add("デバッグ情報", LogLevel.DEBUG)
    output_manager.add("警告メッセージ", LogLevel.WARNING, 
                      formatinfo=FormatInfo(color="yellow", bold=True))
    
    # Output results
    print("=== Production Output ===")
    output_manager.flush()


def test_example():
    """Test usage example with mock."""
    # Setup test DI container
    container = DIContainer()
    configure_test_dependencies(container)
    
    # Resolve mock logging output manager
    output_manager: OutputManagerInterface = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    
    # Use the mock output manager (no side effects)
    output_manager.add("テスト開始", LogLevel.INFO)
    output_manager.add("テストデータ", LogLevel.DEBUG)
    output_manager.add("テスト完了", LogLevel.INFO)
    
    # For testing, you can access mock-specific methods
    if hasattr(output_manager, 'get_captured_outputs'):
        print("=== Test Mock Verification ===")
        print(f"Captured outputs: {len(output_manager.get_captured_outputs())}")
        print(f"Flush calls: {output_manager.get_flush_count()}")


def class_injection_example():
    """Example of injecting output manager into a service class."""
    
    class LoggingService:
        """Service that depends on OutputManagerInterface."""
        
        def __init__(self, output_manager: OutputManagerInterface):
            self.output_manager = output_manager
        
        def start_operation(self, operation_name: str):
            """Start an operation with logging."""
            self.output_manager.add(f"操作開始: {operation_name}", LogLevel.INFO)
        
        def complete_operation(self, operation_name: str, success: bool = True):
            """Complete an operation with logging."""
            if success:
                self.output_manager.add(f"操作完了: {operation_name}", LogLevel.INFO, 
                                      formatinfo=FormatInfo(color="green"))
            else:
                self.output_manager.add(f"操作失敗: {operation_name}", LogLevel.ERROR,
                                      formatinfo=FormatInfo(color="red", bold=True))
        
        def generate_report(self) -> str:
            """Generate operation report."""
            return self.output_manager.output(level=LogLevel.INFO)
    
    # Production usage
    container = DIContainer()
    configure_production_dependencies(container)
    
    output_manager = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    service = LoggingService(output_manager)
    
    service.start_operation("データ処理")
    service.complete_operation("データ処理", success=True)
    
    print("=== Service Report ===")
    print(service.generate_report())


if __name__ == "__main__":
    print("DI注入可能なLogging使用例\n")
    
    production_example()
    print()
    
    test_example()
    print()
    
    class_injection_example()