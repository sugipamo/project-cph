#!/usr/bin/env python3
"""
純粋関数移行による性能影響の測定
"""
import time
import statistics
from typing import Dict, Any
from src.operations.utils.pure_functions import (
    format_string_pure,
    build_docker_run_command_pure,
    validate_docker_image_name_pure
)

def benchmark_function(func, *args, iterations=1000):
    """関数の性能を測定"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        times.append(end - start)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }

def manual_format_string(value: str, context: Dict[str, str]) -> str:
    """純粋関数を使わない直接実装"""
    result = value
    for key, val in context.items():
        result = result.replace(f"{{{key}}}", str(val))
    return result

def manual_docker_run_command(image: str, name: str = None, options: Dict[str, Any] = None):
    """純粋関数を使わない直接実装"""
    cmd = ["docker", "run", "-d"]
    if name:
        cmd.extend(["--name", name])
    if options:
        for key, value in options.items():
            if len(key) == 1:
                cmd.append(f"-{key}")
            else:
                cmd.append(f"--{key.replace('_', '-')}")
            if value is not None and value != "":
                cmd.append(str(value))
    cmd.extend([image, "tail", "-f", "/dev/null"])
    return cmd

def main():
    print("🔬 純粋関数移行の性能影響測定")
    print("=" * 50)
    
    # テストデータ
    template = "Hello {name}, you are in {env_type} environment running {language}"
    context = {"name": "test", "env_type": "local", "language": "python"}
    
    image = "ubuntu:20.04"
    container_name = "test-container"
    docker_options = {"v": "/host:/container", "p": "8080:80"}
    
    # 文字列フォーマットの性能比較
    print("\n📝 文字列フォーマット性能比較:")
    
    pure_stats = benchmark_function(format_string_pure, template, context)
    manual_stats = benchmark_function(manual_format_string, template, context)
    
    print(f"純粋関数: {pure_stats['mean']*1000:.3f}ms (±{pure_stats['stdev']*1000:.3f}ms)")
    print(f"直接実装: {manual_stats['mean']*1000:.3f}ms (±{manual_stats['stdev']*1000:.3f}ms)")
    print(f"オーバーヘッド: {(pure_stats['mean']/manual_stats['mean']-1)*100:.1f}%")
    
    # Dockerコマンド構築の性能比較
    print("\n🐳 Dockerコマンド構築性能比較:")
    
    pure_docker_stats = benchmark_function(build_docker_run_command_pure, image, container_name, docker_options)
    manual_docker_stats = benchmark_function(manual_docker_run_command, image, container_name, docker_options)
    
    print(f"純粋関数: {pure_docker_stats['mean']*1000:.3f}ms (±{pure_docker_stats['stdev']*1000:.3f}ms)")
    print(f"直接実装: {manual_docker_stats['mean']*1000:.3f}ms (±{manual_docker_stats['stdev']*1000:.3f}ms)")
    print(f"オーバーヘッド: {(pure_docker_stats['mean']/manual_docker_stats['mean']-1)*100:.1f}%")
    
    # バリデーション関数の性能測定
    print("\n✅ バリデーション関数性能:")
    
    validation_stats = benchmark_function(validate_docker_image_name_pure, "ubuntu:20.04")
    print(f"イメージ名検証: {validation_stats['mean']*1000:.3f}ms (±{validation_stats['stdev']*1000:.3f}ms)")
    
    # 全体的な性能影響評価
    print("\n📊 性能影響評価:")
    avg_overhead = ((pure_stats['mean']/manual_stats['mean']) + 
                   (pure_docker_stats['mean']/manual_docker_stats['mean'])) / 2
    
    if avg_overhead < 1.1:
        print("✅ 性能オーバーヘッドは許容範囲内（10%以下）")
    elif avg_overhead < 1.5:
        print("⚠️ 軽微な性能オーバーヘッドあり（10-50%）")
    else:
        print("❌ 重大な性能オーバーヘッドあり（50%以上）")
    
    print(f"平均オーバーヘッド: {(avg_overhead-1)*100:.1f}%")
    
    # 推奨事項
    print("\n💡 推奨事項:")
    if avg_overhead < 1.2:
        print("- 純粋関数の使用を継続することを推奨")
        print("- 関数型プログラミングの利点がオーバーヘッドを上回る")
    else:
        print("- 高頻度で呼び出される箇所では直接実装を検討")
        print("- キャッシュ機能の導入を検討")
        print("- クリティカルパスでは性能プロファイリングを実施")

if __name__ == "__main__":
    main()