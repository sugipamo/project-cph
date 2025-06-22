# デバッグ機能とoutput_presetsの統一計画

## 現状分析

### 現在の構造

#### 1. output_presets の構造
```json
"output_presets": {
  "quiet": {
    "description": "最小限の出力",
    "show_workflow_summary": false,
    "show_step_details": false,
    "show_execution_completion": false
  },
  "summary_only": {
    "description": "サマリーのみ表示",
    "show_workflow_summary": true,
    "show_step_details": false,
    "show_execution_completion": false
  },
  "minimal_details": {
    "description": "最小限の詳細表示",
    "show_workflow_summary": true,
    "show_step_details": true,
    "show_execution_completion": false,
    "step_details": { ... }
  },
  "verbose": {
    "description": "詳細な出力",
    "show_workflow_summary": true,
    "show_step_details": true,
    "show_execution_completion": true,
    "step_details": { ... }
  }
}
```

#### 2. 現在のデフォルト出力設定
```json
"output": {
  "show_execution_settings": true,
  "show_workflow_summary": true,
  "show_step_details": false,
  "show_execution_completion": true,
  "step_details": { ... }
}
```

#### 3. 現在のデバッグ機能の問題点
- `DebugService`が直接`output.show_step_details`を変更
- `output_presets`システムと連携していない
- デバッグモードが単独で動作し、既存のプリセットシステムを無視

## 統一戦略

### 1. デバッグプリセットの追加

#### 新しいプリセット構造
```json
"output_presets": {
  "quiet": { ... },
  "summary_only": { ... },
  "minimal_details": { ... },
  "verbose": { ... },
  "debug": {
    "description": "デバッグモード専用の詳細出力",
    "show_workflow_summary": true,
    "show_step_details": true,
    "show_execution_completion": true,
    "show_execution_settings": true,
    "step_details": {
      "show_type": true,
      "show_command": true,
      "show_path": true,
      "show_execution_time": true,
      "show_stdout": true,
      "show_stderr": true,
      "show_return_code": true,
      "max_command_length": 200,
      "show_debug_context": true,
      "show_logger_levels": true
    },
    "debug_specific": {
      "show_debug_messages": true,
      "show_context_details": true,
      "show_infrastructure_state": true,
      "show_service_registrations": true
    }
  }
}
```

### 2. 設定適用メカニズムの統一

#### 現在の問題
- `RuntimeConfigOverlay`が個別設定を直接変更
- プリセットシステムとの連携がない

#### 解決策：PresetManager の導入

```
src/infrastructure/config/
├── runtime_config_overlay.py    # 既存
├── preset_manager.py            # 新規追加
└── debug_preset_controller.py   # 新規追加
```

### 3. 実装計画

#### Phase 1: PresetManager の実装

**ファイル**: `src/infrastructure/config/preset_manager.py`

```python
class PresetManager:
    """出力プリセットの管理クラス"""
    
    def __init__(self, config_manager, overlay: RuntimeConfigOverlay):
        self.config_manager = config_manager
        self.overlay = overlay
        self._active_preset = None
        
    def apply_preset(self, preset_name: str) -> bool:
        """指定されたプリセットを適用"""
        
    def get_available_presets(self) -> List[str]:
        """利用可能なプリセット一覧を取得"""
        
    def get_current_preset(self) -> Optional[str]:
        """現在適用中のプリセット名を取得"""
        
    def restore_default(self) -> None:
        """デフォルト設定に復元"""
```

#### Phase 2: DebugPresetController の実装

**ファイル**: `src/infrastructure/config/debug_preset_controller.py`

```python
class DebugPresetController:
    """デバッグ専用プリセット制御"""
    
    def __init__(self, preset_manager: PresetManager):
        self.preset_manager = preset_manager
        self._pre_debug_preset = None
        
    def enable_debug_preset(self) -> None:
        """デバッグプリセットを有効化し、現在の設定を保存"""
        
    def disable_debug_preset(self) -> None:
        """デバッグプリセットを無効化し、元の設定を復元"""
        
    def is_debug_preset_active(self) -> bool:
        """デバッグプリセットがアクティブかチェック"""
```

#### Phase 3: DebugService の改修

**修正対象**: `src/infrastructure/debug/debug_service.py`

```python
class DebugService:
    def __init__(self, infrastructure: DIContainer):
        self.infrastructure = infrastructure
        self.overlay = RuntimeConfigOverlay()
        self.config_provider = DebugConfigProvider(self.overlay)
        
        # プリセット制御の追加
        self.preset_manager = self._create_preset_manager()
        self.debug_preset_controller = DebugPresetController(self.preset_manager)
        
        self._debug_enabled = False
    
    def enable_debug_mode(self) -> None:
        """デバッグモードを有効化"""
        if self._debug_enabled:
            return
            
        # 1. デバッグプリセットを適用
        self.debug_preset_controller.enable_debug_preset()
        
        # 2. ロガーレベルを更新
        self._update_logger_levels()
        
        # 3. デバッグ状態を記録
        self._debug_enabled = True
        
        # 4. デバッグ開始メッセージ
        self._show_debug_notification()
    
    def disable_debug_mode(self) -> None:
        """デバッグモードを無効化"""
        if not self._debug_enabled:
            return
            
        # プリセットを元に戻す
        self.debug_preset_controller.disable_debug_preset()
        self._debug_enabled = False
```

### 4. コマンドラインオプションの拡張

#### --debug-preset オプションの追加

```bash
# デフォルトのデバッグプリセット使用
./cph.sh abc300 open a local python --debug

# 特定のプリセットを指定
./cph.sh abc300 open a local python --preset verbose
./cph.sh abc300 open a local python --preset debug

# デバッグモード + カスタムプリセット
./cph.sh abc300 open a local python --debug --preset minimal_details
```

#### 引数解析の拡張

**修正対象**: `src/context/user_input_parser/user_input_parser.py`

```python
def _scan_and_apply_options(args, context, infrastructure):
    """コマンドラインオプションを検出・処理する"""
    debug_enabled = False
    preset_name = None
    filtered_args = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--debug":
            debug_enabled = True
        elif arg == "--preset" and i + 1 < len(args):
            preset_name = args[i + 1]
            i += 1  # 次の引数もスキップ
        else:
            filtered_args.append(arg)
        i += 1
    
    if debug_enabled or preset_name:
        context.debug_mode = debug_enabled
        context.preset_name = preset_name
        _apply_output_configuration(infrastructure, debug_enabled, preset_name)
    
    return filtered_args, context
```

### 5. 設定ファイルの拡張

#### env.json への追加

```json
{
  "output_presets": {
    "quiet": { ... },
    "summary_only": { ... },
    "minimal_details": { ... },
    "verbose": { ... },
    "debug": {
      "description": "デバッグモード専用の詳細出力",
      "show_workflow_summary": true,
      "show_step_details": true,
      "show_execution_completion": true,
      "show_execution_settings": true,
      "step_details": {
        "show_type": true,
        "show_command": true,
        "show_path": true,
        "show_execution_time": true,
        "show_stdout": true,
        "show_stderr": true,
        "show_return_code": true,
        "max_command_length": 200,
        "show_debug_context": true,
        "show_logger_levels": true
      },
      "debug_specific": {
        "show_debug_messages": true,
        "show_context_details": true,
        "show_infrastructure_state": true,
        "show_service_registrations": true
      }
    }
  },
  "preset_defaults": {
    "default_preset": "summary_only",
    "debug_preset": "debug",
    "fallback_preset": "summary_only"
  }
}
```

### 6. 互換性の確保

#### 既存動作の保持

1. **既存のコマンド**: `./cph.sh abc300 open a local python --debug`
   - 動作変更なし（デバッグプリセット自動適用）

2. **設定ファイル**: `contest_env/shared/env.json`
   - 既存の`output`設定は維持
   - 新しい`output_presets.debug`を追加

3. **API互換性**: 
   - `DebugService`の既存メソッドは維持
   - 内部実装のみプリセットシステムを使用

### 7. 実装順序

#### Step 1: 基盤実装 (1日)
1. `PresetManager`クラスの実装
2. `DebugPresetController`クラスの実装
3. 基本的なテストケース作成

#### Step 2: デバッグプリセット追加 (半日)
1. `env.json`に`debug`プリセット追加
2. プリセット読み込み機能の実装

#### Step 3: DebugService統合 (半日)
1. `DebugService`の改修
2. プリセットシステムとの統合

#### Step 4: コマンドライン拡張 (半日)
1. `--preset`オプションの追加
2. 引数解析ロジックの拡張

#### Step 5: テスト・検証 (半日)
1. 統合テストの実行
2. 既存機能の動作確認
3. 新機能の動作確認

### 8. 期待される効果

#### 一貫性の向上
- 出力制御が統一されたプリセットシステムで管理
- デバッグ機能が既存の設定システムと整合

#### 柔軟性の向上
- ユーザーが出力レベルを細かく制御可能
- デバッグ時も任意のプリセットを選択可能

#### 保守性の向上
- 出力設定の変更が一箇所で管理
- プリセットの追加・変更が容易

### 9. リスク管理

#### 下位互換性
- 既存のコマンドライン引数は維持
- 既存の設定ファイル構造は維持

#### 段階的移行
- 新機能は既存機能に上乗せ
- 問題発生時は既存機能にフォールバック

#### テスト戦略
- 既存機能の回帰テスト必須
- 新機能の単体・統合テスト実施