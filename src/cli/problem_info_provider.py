import os
from typing import Dict, Any, List

def get_problem_info(
    contest_name: str,
    problem_name: str,
    env_type: str,
    oj_env: dict,
    client,
    dest_dir: str = "./test"
) -> Dict[str, Any]:
    """
    テストケースを取得し、dest_dir配下に保存する
    - contest_name, problem_name, env_type: 問題指定
    - oj_env: 環境設定
    - client: ファイル取得API（client.get_file(remote_path, local_path)を持つ想定）
    - dest_dir: 保存先ディレクトリ（例: ./test）
    戻り値: {"success": bool, "files": List[str], "error": str}
    """
    try:
        handler = oj_env["handlers"][env_type]
        # テストケースリスト取得コマンド
        list_cmd_tpl = handler["list_cases_cmd"]  # 例: ["ls", "/problems/{contest_name}_{problem_name}/cases"]
        context = {"contest_name": contest_name, "problem_name": problem_name}
        list_cmd = [s.format(**context) for s in list_cmd_tpl]
        # テストケースファイル一覧を取得
        case_list_result = client.run(list_cmd)
        case_files = case_list_result.stdout.strip().splitlines()
        os.makedirs(dest_dir, exist_ok=True)
        saved_files: List[str] = []
        for fname in case_files:
            remote_path = handler["case_path_tpl"].format(
                contest_name=contest_name, problem_name=problem_name, filename=fname
            )
            local_path = os.path.join(dest_dir, fname)
            client.get_file(remote_path, local_path)
            saved_files.append(local_path)
        return {"success": True, "files": saved_files}
    except Exception as e:
        return {"success": False, "error": str(e)} 