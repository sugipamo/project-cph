from typing import Any, Dict, List

def open_problem(
    contest_name: str,
    problem_name: str,
    api_client,
    file_manager,
    *,
    dest_dir: str,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    問題を開く（APIから取得しローカルに保存）
    Parameters:
        contest_name: コンテスト名（例: "abc123"）
        problem_name: 問題名（例: "a", "b"）
        api_client: 問題情報取得用の関数またはクライアント
        file_manager: ファイル操作用の関数群
        dest_dir: 保存先ディレクトリ
        overwrite: 既存ファイルを上書きするか
    Returns:
        {
            "success": bool,
            "path": str,         # 保存先ディレクトリ
            "files": list,       # 保存したファイルのリスト
            "error": str         # エラー時のみ
        }
    """
    try:
        # 問題情報取得
        problem = api_client.get_problem_info(contest_name, problem_name)
        if not problem:
            return {"success": False, "error": "問題情報が取得できません"}
        # ディレクトリ作成
        file_manager.make_dir(dest_dir)
        saved_files: List[str] = []
        # README.md保存
        readme_path = file_manager.join(dest_dir, "README.md")
        if not file_manager.file_exists(readme_path) or overwrite:
            file_manager.write_file(readme_path, problem["description"])
            saved_files.append(readme_path)
        # サンプルケース保存
        for i, case in enumerate(problem.get("samples", []), 1):
            in_path = file_manager.join(dest_dir, f"sample_{i}.in")
            out_path = file_manager.join(dest_dir, f"sample_{i}.out")
            if not file_manager.file_exists(in_path) or overwrite:
                file_manager.write_file(in_path, case["input"])
                saved_files.append(in_path)
            if not file_manager.file_exists(out_path) or overwrite:
                file_manager.write_file(out_path, case["output"])
                saved_files.append(out_path)
        return {"success": True, "path": dest_dir, "files": saved_files}
    except Exception as e:
        return {"success": False, "error": str(e)} 