from contest_env.base import LanguageConfig

def test_default_values():
    config = LanguageConfig(name='python')
    assert config.name == 'python'
    assert config.build_cmd is None
    assert config.run_cmd is None
    assert config.bin_path is None
    assert config.source_file is None
    assert config.copy_mode == 'file'
    assert config.exclude_patterns == []

def test_custom_values():
    config = LanguageConfig(
        name='rust',
        build_cmd=['cargo', 'build'],
        run_cmd=['./main'],
        bin_path='target/release/main',
        source_file='main.rs',
        copy_mode='dir',
        exclude_patterns=['*.tmp', '*.log']
    )
    assert config.name == 'rust'
    assert config.build_cmd == ['cargo', 'build']
    assert config.run_cmd == ['./main']
    assert config.bin_path == 'target/release/main'
    assert config.source_file == 'main.rs'
    assert config.copy_mode == 'dir'
    assert config.exclude_patterns == ['*.tmp', '*.log'] 