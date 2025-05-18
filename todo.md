# UserInputParser 実装方針・要件まとめ

## 目的
- CLI等から渡される順不同の引数リストから、
  必須情報（command, language, env_type, contest_name, problem_name, env_json）を正確に抽出する。

## 要件

### 1. env.json探索
- `context_env`配下の全サブディレクトリを再帰的に探索し、`env.json`を全て読み込む
- 各env.jsonから以下の情報を取得：
  - 言語名（jsonのキー）
  - 言語エイリアス（`aliases`、省略可）
  - env_type名（`env_types`のキー）
  - env_typeエイリアス（`aliases`、省略可）
  - command名（`commands`のキー）
  - commandエイリアス（`aliases`、省略可）

### 2. 入力リストのパース
- 入力はリスト形式（例: `['test', 'abc301', 'a', 'python', 'local']`）
- 順序は完全自由
- どの位置にあっても良い

### 3. 判定・割り当て
- 入力リストから順不同で各要素を判定
  - command, language, env_typeは、名称またはエイリアスと一致するものを探す
  - 一致したものは「使用済み」としてマーク
- contest_name, problem_nameは未使用部分を左から順に割り当て
- 余剰引数があればエラー

### 4. 必須項目
- `command`, `language`, `env_type`, `contest_name`, `problem_name`が全て揃わなければエラー
- contest_name, problem_nameは未使用部分を左から順に割り当て
- 余剰引数があればエラー

### 5. エイリアス
- `aliases`は省略可能
- jsonのキー（例: `"python"`, `"rust"`）がメイン名称
- エイリアスがなければメイン名称のみで判定

### 6. エラー時の挙動
- 必須項目が1つでも見つからなかった場合は即エラー
- contest_name, problem_name以外の未使用引数があればエラー

## 実装イメージ
- `UserInputParser.parse(args: list) -> dict`
  - 必須情報（command, language, env_type, contest_name, problem_name, env_json）を返す
  - 不足時や余剰引数時は例外を投げる

## 今後のタスク
- context_env配下のenv.json探索・情報抽出ロジック実装
- 入力リストのパース・割り当てロジック実装
- エラー処理・テストケース作成

## 必要クラス設計案

### 1. UserInputParser
- **役割**: CLI等から渡される引数リストをパースし、必須情報を抽出・バリデーションする
- **主要プロパティ**:
  - env_json_list: List[dict]  # context_env配下から集めたenv.jsonのリスト
- **主要メソッド**:
  - parse(args: list) -> UserInputParseResult
  - _load_env_jsons() -> None
  - _find_language(args: list) -> (str, dict)
  - _find_env_type(args: list, env_json: dict) -> str
  - _find_command(args: list, env_json: dict) -> str
  - _find_contest_and_problem(args: list, used_indices: set) -> (str, str)

### 2. UserInputParseResult
- **役割**: パース結果（必須情報）を保持するデータクラス
- **主要プロパティ**:
  - command: str
  - language: str
  - env_type: str
  - contest_name: str
  - problem_name: str
  - env_json: dict
- **主要メソッド**:
  - なし（データ保持のみ）

### 3. EnvJsonInfo（補助クラス・必要に応じて）
- **役割**: 1つのenv.jsonから抽出した言語名・エイリアス・env_type・command等の情報をまとめて保持
- **主要プロパティ**:
  - language: str
  - language_aliases: List[str]
  - env_types: Dict[str, List[str]]  # env_type名→エイリアス
  - commands: Dict[str, List[str]]   # command名→エイリアス
  - raw_json: dict
- **主要メソッド**:
  - なし（データ保持のみ）

---

※設計・命名は今後の実装や運用で調整可能です。
