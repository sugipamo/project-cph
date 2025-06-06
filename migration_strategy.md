# 既存コードとの互換性を保つマイグレーション戦略

## 🎯 マイグレーション目標

1. **ゼロダウンタイム**: 既存機能の動作を一切破綻させない
2. **段階的移行**: フェーズごとに安全に移行
3. **フォールバック**: 問題発生時の自動復旧
4. **テスト駆動**: 各段階でテストによる検証

## 🔄 マイグレーション戦略

### Phase 0: 準備フェーズ (2-3h)

#### 1. 既存動作の完全テスト化
```python
# tests/migration/test_existing_behavior.py
class TestExistingTestBehavior:
    """既存のテスト動作を完全にキャプチャ"""
    
    def test_current_detailed_output_format(self):
        """現在の詳細出力フォーマットをテスト"""
        # 既存の出力形式を正確にキャプチャ
        expected_output = """Testing sample-1.in
✓ PASS
Testing sample-2.in
✗ FAIL
Expected:
2
Got:
1"""
        # 実際の実行結果と比較
        assert self._run_current_test() == expected_output
    
    def test_current_error_output_format(self):
        """現在のエラー出力フォーマットをテスト"""
        expected_output = """Testing sample-3.in
✗ ERROR
Program failed with error:
ValueError: invalid literal for int()"""
        assert self._run_current_error_test() == expected_output
    
    def test_current_env_json_compatibility(self):
        """現在のenv.json設定との互換性テスト"""
        # 既存のenv.json設定が引き続き動作することを確認
        pass
```

#### 2. アダプターパターンによる互換性レイヤー
```python
# src/operations/formatters/compatibility_adapter.py
class LegacyTestFormatterAdapter:
    """既存のテストフォーマット機能との互換性を保つアダプター"""
    
    def __init__(self, new_formatter_factory: FormatterFactory):
        self.new_factory = new_formatter_factory
        self.legacy_mode = True  # デフォルトはレガシーモード
    
    def generate_legacy_test_script(self, formatted_cmd: List[str], 
                                  contest_current_path: str) -> str:
        """既存のテストスクリプト生成ロジックを完全再現"""
        if self.legacy_mode:
            # 既存のbashスクリプト生成ロジックをそのまま使用
            return self._generate_original_script(formatted_cmd, contest_current_path)
        else:
            # 新しいフォーマッタシステムを使用
            return self._generate_new_script(formatted_cmd, contest_current_path)
    
    def _generate_original_script(self, formatted_cmd: List[str], 
                                contest_current_path: str) -> str:
        """オリジナルスクリプト生成（完全に既存のコードをコピー）"""
        return f'''
        for i in {contest_current_path}/test/sample-*.in; do
            if [ -f "$i" ]; then
                echo "Testing $(basename "$i")"
                expected="${{i%.in}}.out"
                if [ -f "$expected" ]; then
                    if {' '.join(formatted_cmd)} < "$i" > output.tmp 2>error.tmp; then
                        if diff -q output.tmp "$expected" > /dev/null 2>&1; then
                            echo "✓ PASS"
                        else
                            echo "✗ FAIL"
                            echo "Expected:"
                            cat "$expected"
                            echo "Got:"
                            cat output.tmp
                        fi
                    else
                        echo "✗ ERROR"
                        echo "Program failed with error:"
                        cat error.tmp
                    fi
                    rm -f output.tmp error.tmp
                else
                    echo "Expected output file not found: $expected"
                fi
            else
                echo "No test files found"
            fi
        done
        '''
```

### Phase 1: 新システム導入（既存動作保持） (6-8h)

#### 1. 新旧システムの並行実装
```python
# src/operations/factory/unified_request_factory.py (修正版)
class ComplexRequestStrategy(RequestCreationStrategy):
    """既存機能を保持しつつ新機能を導入"""
    
    def __init__(self):
        # フィーチャーフラグで新旧システムを切り替え
        self.use_new_formatter = os.getenv('USE_NEW_FORMATTER', 'false').lower() == 'true'
        
        if self.use_new_formatter:
            from src.operations.formatters.compatibility_adapter import LegacyTestFormatterAdapter
            from src.operations.formatters.formatter_factory import FormatterFactory
            self.adapter = LegacyTestFormatterAdapter(FormatterFactory())
        
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        if step.type == StepType.TEST:
            formatted_cmd = self._format_step_values(step.cmd, context)
            contest_current_path = self._format_value('{contest_current_path}', context)
            
            if self.use_new_formatter and self._has_format_options(step):
                # 新しいフォーマッタシステムを使用
                test_script = self._create_new_test_script(step, formatted_cmd, contest_current_path)
            else:
                # 既存のテストスクリプト生成（完全に既存の動作）
                test_script = self._create_legacy_test_script(formatted_cmd, contest_current_path)
            
            return ShellRequest(
                cmd=['bash', '-c', test_script],
                timeout=env_manager.get_timeout(),
                cwd=self._format_value(step.cwd, context) if step.cwd else env_manager.get_working_directory(),
                env=getattr(step, 'env', None),
                allow_failure=getattr(step, 'allow_failure', False)
            )
    
    def _has_format_options(self, step: Step) -> bool:
        """ステップに新しいフォーマットオプションが含まれているかチェック"""
        step_dict = step.__dict__ if hasattr(step, '__dict__') else {}
        return ('output_format' in step_dict or 'format_options' in step_dict)
    
    def _create_legacy_test_script(self, formatted_cmd: List[str], contest_current_path: str) -> str:
        """既存のテストスクリプト生成ロジック（変更なし）"""
        # 既存のコードをそのままコピー
        return f'''
        for i in {contest_current_path}/test/sample-*.in; do
            if [ -f "$i" ]; then
                echo "Testing $(basename "$i")"
                expected="${{i%.in}}.out"
                if [ -f "$expected" ]; then
                    if {' '.join(formatted_cmd)} < "$i" > output.tmp 2>error.tmp; then
                        if diff -q output.tmp "$expected" > /dev/null 2>&1; then
                            echo "✓ PASS"
                        else
                            echo "✗ FAIL"
                            echo "Expected:"
                            cat "$expected"
                            echo "Got:"
                            cat output.tmp
                        fi
                    else
                        echo "✗ ERROR"
                        echo "Program failed with error:"
                        cat error.tmp
                    fi
                    rm -f output.tmp error.tmp
                else
                    echo "Expected output file not found: $expected"
                fi
            else
                echo "No test files found"
            fi
        done
        '''
    
    def _create_new_test_script(self, step: Step, formatted_cmd: List[str], contest_current_path: str) -> str:
        """新しいフォーマッタシステムを使用したスクリプト生成"""
        from src.operations.formatters.config_integration import FormatConfigResolver
        
        step_dict = step.__dict__ if hasattr(step, '__dict__') else {}
        format_options = FormatConfigResolver.resolve_format_options(step_dict)
        
        # 新しいフォーマッタを使用してスクリプト生成
        # （実装の詳細は新システムに依存）
        return self.adapter.generate_enhanced_test_script(formatted_cmd, contest_current_path, format_options)
```

#### 2. 環境変数による機能切り替え
```bash
# .env または環境設定
USE_NEW_FORMATTER=false  # デフォルトは既存動作
NEW_FORMATTER_DEBUG=true # デバッグモード
```

#### 3. 包括的テストスイート
```python
# tests/migration/test_compatibility.py
class TestBackwardCompatibility:
    """後方互換性の包括的テスト"""
    
    def test_default_behavior_unchanged(self):
        """デフォルトの動作が変わらないことを確認"""
        # USE_NEW_FORMATTER=false の状態で
        # 既存の動作と完全に同じ出力が得られることを確認
        pass
    
    def test_env_json_compatibility(self):
        """既存のenv.json設定がそのまま動作することを確認"""
        pass
    
    def test_command_line_compatibility(self):
        """既存のコマンドライン引数がそのまま動作することを確認"""
        pass
```

### Phase 2: 段階的な新機能公開 (4-6h)

#### 1. オプトイン形式での新機能提供
```json
// contest_env/python/env.json - 新機能をオプトインで提供
{
  "python": {
    "commands": {
      "test": {
        "aliases": ["t"],
        "description": "テストを実行する",
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"]
            // フォーマットオプションなし = 既存動作
          }
        ]
      },
      "test_new": {
        "aliases": ["tn"],
        "description": "新しいフォーマッタでテスト実行",
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "detailed",  // 新機能を明示的に有効化
            "format_options": {
              "show_timing": true
            }
          }
        ]
      }
    }
  }
}
```

#### 2. 段階的な機能有効化
```python
# src/operations/formatters/migration_manager.py
class MigrationManager:
    """マイグレーションの段階的な管理"""
    
    def __init__(self):
        self.phase = self._get_migration_phase()
    
    def _get_migration_phase(self) -> str:
        """現在のマイグレーションフェーズを取得"""
        return os.getenv('MIGRATION_PHASE', 'legacy')
    
    def should_use_new_formatter(self, step_config: Dict) -> bool:
        """新しいフォーマッタを使用すべきかの判定"""
        if self.phase == 'legacy':
            # レガシーモード: 明示的な設定がある場合のみ新システム
            return 'output_format' in step_config
        elif self.phase == 'transition':
            # 移行モード: デフォルトは新システム、オプトアウト可能
            return step_config.get('use_legacy_formatter', False) is False
        elif self.phase == 'new':
            # 新システムモード: 常に新システム
            return True
        else:
            # 不明なフェーズ: 安全側に倒してレガシー
            return False
```

### Phase 3: デフォルト切り替え (2-3h)

#### 1. デフォルト動作の段階的変更
```python
# src/operations/formatters/default_behavior.py
class DefaultBehaviorManager:
    """デフォルト動作の段階的な変更管理"""
    
    @staticmethod
    def get_default_format_options() -> FormatOptions:
        """段階的にデフォルトを変更"""
        migration_phase = os.getenv('MIGRATION_PHASE', 'legacy')
        
        if migration_phase == 'legacy':
            # 既存動作と完全に同じフォーマット
            return FormatOptions(
                format_type='legacy',  # 特別なレガシーフォーマット
                show_colors=False,     # 既存は色なし
                show_timing=False,     # 既存はタイミングなし
                show_diff=True         # 既存は差分表示あり
            )
        elif migration_phase == 'enhanced_legacy':
            # 既存動作 + 小さな改善
            return FormatOptions(
                format_type='detailed',
                show_colors=True,      # 色を追加
                show_timing=False,
                show_diff=True
            )
        else:
            # 完全な新システム
            return FormatOptions(
                format_type='detailed',
                show_colors=True,
                show_timing=True,      # タイミング表示追加
                show_diff=True
            )
```

### Phase 4: レガシーコード削除 (1-2h)

#### 1. 段階的なクリーンアップ
```python
# src/operations/formatters/cleanup_manager.py
class LegacyCleanupManager:
    """レガシーコードの安全な削除管理"""
    
    def __init__(self):
        self.cleanup_phase = os.getenv('CLEANUP_PHASE', 'none')
    
    def can_remove_legacy_code(self) -> bool:
        """レガシーコードの削除可能性チェック"""
        # 一定期間新システムで問題なく動作していることを確認
        return (self.cleanup_phase == 'final' and 
                self._verify_new_system_stability())
    
    def _verify_new_system_stability(self) -> bool:
        """新システムの安定性検証"""
        # メトリクス収集、ユーザーフィードバック等をチェック
        return True
```

## 🔒 安全策とフォールバック

### 1. 自動フォールバック機能
```python
# src/operations/formatters/safety_wrapper.py
class SafetyWrapper:
    """新システムでエラーが発生した場合の自動フォールバック"""
    
    def __init__(self, new_formatter, legacy_formatter):
        self.new_formatter = new_formatter
        self.legacy_formatter = legacy_formatter
        self.fallback_count = 0
        self.max_fallbacks = 3
    
    def format_with_fallback(self, *args, **kwargs):
        """新システムでエラーが発生した場合、自動的にレガシーにフォールバック"""
        try:
            return self.new_formatter.format(*args, **kwargs)
        except Exception as e:
            self.fallback_count += 1
            if self.fallback_count <= self.max_fallbacks:
                logger.warning(f"New formatter failed, falling back to legacy: {e}")
                return self.legacy_formatter.format(*args, **kwargs)
            else:
                raise e
```

### 2. 設定検証とエラー処理
```python
# src/operations/formatters/config_validator.py
class ConfigValidator:
    """設定の妥当性検証"""
    
    @staticmethod
    def validate_format_config(config: Dict) -> Tuple[bool, List[str]]:
        """フォーマット設定の妥当性をチェック"""
        errors = []
        
        if 'output_format' in config:
            valid_formats = ['detailed', 'compact', 'json', 'legacy']
            if config['output_format'] not in valid_formats:
                errors.append(f"Invalid output_format: {config['output_format']}")
        
        if 'format_options' in config:
            options = config['format_options']
            if not isinstance(options, dict):
                errors.append("format_options must be a dictionary")
        
        return len(errors) == 0, errors
```

## 📊 マイグレーション監視

### 1. メトリクス収集
```python
# src/operations/formatters/migration_metrics.py
class MigrationMetrics:
    """マイグレーションの進行状況監視"""
    
    def __init__(self):
        self.metrics = {
            'legacy_usage': 0,
            'new_system_usage': 0,
            'fallback_count': 0,
            'error_count': 0
        }
    
    def record_formatter_usage(self, formatter_type: str):
        """フォーマッタ使用状況の記録"""
        if formatter_type == 'legacy':
            self.metrics['legacy_usage'] += 1
        else:
            self.metrics['new_system_usage'] += 1
    
    def record_fallback(self):
        """フォールバック発生の記録"""
        self.metrics['fallback_count'] += 1
    
    def get_migration_progress(self) -> float:
        """マイグレーション進捗の計算"""
        total = self.metrics['legacy_usage'] + self.metrics['new_system_usage']
        if total == 0:
            return 0.0
        return self.metrics['new_system_usage'] / total
```

## 🧪 包括的テスト戦略

### 1. マイグレーション専用テストスイート
```python
# tests/migration/test_migration_suite.py
class MigrationTestSuite:
    """マイグレーション全体の包括的テスト"""
    
    def test_phase_0_legacy_preservation(self):
        """Phase 0: 既存動作の完全保持"""
        pass
    
    def test_phase_1_parallel_execution(self):
        """Phase 1: 新旧システムの並行動作"""
        pass
    
    def test_phase_2_gradual_rollout(self):
        """Phase 2: 段階的な新機能公開"""
        pass
    
    def test_phase_3_default_migration(self):
        """Phase 3: デフォルト動作の変更"""
        pass
    
    def test_fallback_mechanisms(self):
        """フォールバック機能のテスト"""
        pass
    
    def test_config_validation(self):
        """設定検証機能のテスト"""
        pass
```

## 📅 実装タイムライン

| フェーズ | 期間 | 主要作業 | リスク |
|----------|------|----------|--------|
| Phase 0 | 2-3h | 既存動作テスト化、アダプター作成 | 低 |
| Phase 1 | 6-8h | 新システム導入、並行実行 | 中 |
| Phase 2 | 4-6h | 段階的新機能公開 | 中 |
| Phase 3 | 2-3h | デフォルト切り替え | 高 |
| Phase 4 | 1-2h | レガシーコード削除 | 低 |
| **合計** | **15-22h** | | |

## ✅ マイグレーション成功基準

1. **機能互換性**: 既存の全テストが引き続きパス
2. **性能劣化なし**: 実行時間が5%以上増加しない
3. **設定互換性**: 既存のenv.json設定がそのまま動作
4. **エラー率**: 新システムでのエラー率が1%未満
5. **ユーザー満足度**: 新機能への移行率が80%以上

この戦略により、既存機能を一切破損させることなく、段階的に新しいフォーマッタシステムに移行できます。