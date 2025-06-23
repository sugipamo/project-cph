# エラー種類別修正方針ガイドライン

## 1. 副作用検出エラー
```python
# 正しい実装：Infrastructure層への委譲
def process_data(data, file_writer):
    file_writer.write_data('output.txt', str(data))
    return data
```

## 2. print文使用エラー
```python
# 正しい実装：Logger使用
def calculate_result(x, y, logger):
    logger.info(f"計算開始: {x} + {y}")
    return x + y
```

## 3. dict.get()使用エラー
```python
# 正しい実装：設定ファイルからの明示的取得
timeout = config['timeout']  # KeyErrorで不備を検出
```

## 4. getattr()デフォルト値エラー
```python
# 正しい実装：明示的な存在チェック
if hasattr(obj, 'attribute'):
    value = obj.attribute
else:
    raise AttributeError("必須属性'attribute'が存在しません")
```

## 5. デフォルト引数使用エラー
```python
# 誤った実装：デフォルト引数使用
def create_user(name, email, role='user'):
    return User(name, email, role)

# 正しい実装：全引数を明示的に要求
def create_user(name, email, role):
    return User(name, email, role)
```

## 6. Infrastructure重複生成エラー
```python
# 誤った実装：毎回新しいインスタンス生成
def get_database():
    return DatabaseConnection()  # 重複生成

# 正しい実装：main.pyからの依存性注入
def process_data(data, database):
    return database.save(data)
```

## 7. フォールバック処理エラー
```python
# 正しい実装：Infrastructure層でのエラー変換
from src.infrastructure.result.error_converter import ErrorConverter

def load_config_safe(error_converter: ErrorConverter):
    return error_converter.execute_with_conversion(load_config)
    
# ビジネスロジック層ではResultを処理
result = load_config_safe(error_converter)
if result.is_failure():
    logger.error(f"設定読み込み失敗: {result.error}")
    raise ConfigurationError("設定ファイルが読み込めません")
```

## 8. 命名規則違反エラー
```python
# 正しい実装：snake_case使用
def calculate_total(items):
    total_price = 0
    return total_price
```

## 10. 設定管理エラー
```python
# 正しい実装：[src|scripts]/configuration/から設定取得
# src/configuration/readme.mdの設定取得方法に従う
```