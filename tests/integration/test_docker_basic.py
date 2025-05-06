import time
import uuid
import pytest
from src.docker.ctl import DockerCtl
import tempfile
import os
from src.docker.pool import DockerPool, generate_container_name, DockerImageManager
import subprocess
from src.contest_file_manager import ContestFileManager
from src.file_operator import LocalFileOperator
from src.commands.command_test import CommandTest
import pathlib
import asyncio
from src.commands.command_open import CommandOpen
from src.commands.opener import MockOpener
import json
import shutil
import subprocess as sp
from pathlib import Path
from src.environment.test_environment import DockerTestExecutionEnvironment

def unique_container_name():
    return f"cph_test_integration_{uuid.uuid4().hex[:8]}"

@pytest.mark.integration
def test_docker_container_lifecycle():
    ctl = DockerCtl(timeout=10)
    name = unique_container_name()
    image = DockerImageManager().ensure_image("oj")  # DockerImageManager経由でojイメージ名を取得

    # 1. コンテナが存在しない状態から開始
    ctl.remove_container(name)  # 念のため削除
    assert not ctl.is_container_running(name)

    # 2. コンテナを起動
    ok = ctl.start_container(name, image)
    assert ok, "コンテナ起動に失敗"
    time.sleep(1)  # 起動待ち
    assert ctl.is_container_running(name), "コンテナが起動していない"

    # 3. execでコマンド実行
    ok, out, err = ctl.exec_in_container(name, ["echo", "hello"])
    assert ok
    assert "hello" in out

    # 4. コンテナを削除
    ok = ctl.remove_container(name)
    assert ok, "コンテナ削除に失敗"
    assert not ctl.is_container_running(name)

def test_docker_volume_mount():
    ctl = DockerCtl(timeout=10)
    name = unique_container_name()
    image = DockerImageManager().ensure_image("oj")
    # 一時ファイル作成
    with tempfile.TemporaryDirectory() as tmpdir:
        host_file = os.path.join(tmpdir, "test.txt")
        with open(host_file, "w") as f:
            f.write("volumetest")
        print("[DEBUG] ホスト側tmpdir:", tmpdir)
        print("[DEBUG] ホスト側ファイル一覧:", os.listdir(tmpdir))
        # tmpdirを/workspaceにマウント
        volumes = {tmpdir: "/workspace"}
        ctl.remove_container(name)
        ok = ctl.start_container(name, image, volumes=volumes)
        assert ok
        # /workspaceの中身を確認
        ok_ls, out_ls, err_ls = ctl.exec_in_container(name, ["ls", "-l", "/workspace"])
        print("[DEBUG] /workspace ls -l (oj):\n", out_ls, err_ls)
        # コンテナ内でcatして内容確認
        ok, out, err = ctl.exec_in_container(name, ["cat", "/workspace/test.txt"])
        print("[DEBUG] cat /workspace/test.txt (oj):", ok, out, err)
        ctl.remove_container(name)

    # python:3イメージでも同様にテスト
    name2 = unique_container_name()
    image2 = "python:3"
    with tempfile.TemporaryDirectory() as tmpdir2:
        host_file2 = os.path.join(tmpdir2, "test.txt")
        with open(host_file2, "w") as f:
            f.write("volumetest")
        print("[DEBUG] ホスト側tmpdir2:", tmpdir2)
        print("[DEBUG] ホスト側ファイル一覧2:", os.listdir(tmpdir2))
        volumes2 = {tmpdir2: "/workspace"}
        ctl.remove_container(name2)
        ok2 = ctl.start_container(name2, image2, volumes=volumes2)
        assert ok2
        ok_ls2, out_ls2, err_ls2 = ctl.exec_in_container(name2, ["ls", "-l", "/workspace"])
        print("[DEBUG] /workspace ls -l (python:3):\n", out_ls2, err_ls2)
        ok2, out2, err2 = ctl.exec_in_container(name2, ["cat", "/workspace/test.txt"])
        print("[DEBUG] cat /workspace/test.txt (python:3):", ok2, out2, err2)
        ctl.remove_container(name2)

def test_docker_start_nonexistent_image():
    ctl = DockerCtl(timeout=10)
    name = unique_container_name()
    image = "this_image_does_not_exist_12345"
    ctl.remove_container(name)
    ok = ctl.start_container(name, image)
    assert not ok, "存在しないイメージで起動が成功してはいけない"
    assert not ctl.is_container_running(name)

def remove_all_cph_containers():
    # cph_で始まる全てのコンテナを強制削除
    result = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True)
    for name in result.stdout.splitlines():
        if name.startswith("cph_"):
            subprocess.run(["docker", "rm", "-f", name])

def test_dockerpool_multiple_containers():
    remove_all_cph_containers()
    pool = DockerPool()
    requirements = [
        {"type": "test", "language": "python", "count": 2},
        {"type": "test", "language": "rust", "count": 1},
        {"type": "ojtools", "count": 1}
    ]
    containers = pool.adjust(requirements)
    # 期待されるコンテナ名
    expected_names = [
        generate_container_name("test", "python", 1),
        generate_container_name("test", "python", 2),
        generate_container_name("test", "rust", 1),
        generate_container_name("ojtools", None, 1)
    ]
    # 実際にdocker psで確認
    result = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True)
    running_names = set(result.stdout.splitlines())
    for name in expected_names:
        assert name in running_names, f"{name} が起動していない"
    # 後始末
    remove_all_cph_containers()

def test_prepare_test_environment_and_collect_cases():
    # contest_current/python/main.py, contest_current/test/*.in,*.out が前提
    file_operator = LocalFileOperator()
    file_manager = ContestFileManager(file_operator)
    tester = CommandTest(file_manager)
    contest_name = "abc300"
    problem_name = "a"
    language_name = "python"
    # 1. 一時ディレクトリ・ファイル準備
    temp_source_path, temp_test_dir = tester.prepare_test_environment(contest_name, problem_name, language_name)
    temp_test_dir = Path(temp_test_dir)
    temp_source_path = Path(temp_source_path)
    # .tempディレクトリが作成されている
    assert os.path.exists(os.path.dirname(temp_source_path))
    # main.pyがコピーされている
    assert os.path.exists(temp_source_path)
    # testディレクトリがコピーされている
    assert os.path.exists(temp_test_dir)
    # テストケース収集
    temp_in_files, out_files = tester.collect_test_cases(temp_test_dir, file_operator)
    assert all(str(f).endswith('.in') for f in temp_in_files)
    assert all(str(f).endswith('.out') for f in out_files)

@pytest.mark.skip(reason="現在調査中のためスキップ")
def test_run_main_py_in_container():
    import os
    import shutil
    from pathlib import Path
    # プロジェクト直下で作業
    # 必要なディレクトリ・ファイルを作成
    if os.path.exists("contest_current"):
        shutil.rmtree("contest_current")
    if os.path.exists(".temp"):
        shutil.rmtree(".temp")
    os.makedirs("contest_current/python", exist_ok=True)
    main_py_path = Path("contest_current/python/main.py")
    main_py_code = (
        "# a.py\n"
        "# 問題: a\n"
        "# 言語: python\n\n"
        "if __name__ == \"__main__\":\n"
        "    import sys\n"
        "    lines = [line.rstrip('\\n') for line in sys.stdin]\n"
        "    if len(lines) >= 2:\n"
        "        print(len(lines[1].split()))\n"
        "    else:\n"
        "        print(0)\n"
    )
    main_py_path.write_text(main_py_code, encoding="utf-8")
    os.makedirs("contest_current/test", exist_ok=True)
    Path("contest_current/test/sample-1.in").write_text("3 125 175\n200 300 400\n", encoding="utf-8")
    Path("contest_current/test/sample-1.out").write_text("3\n", encoding="utf-8")
    # .tempディレクトリを使う
    if os.path.exists(".temp"):
        shutil.rmtree(".temp")
    os.makedirs(".temp", exist_ok=True)
    file_operator = LocalFileOperator()
    file_manager = ContestFileManager(file_operator)
    tester = CommandTest(file_manager)
    contest_name = "abc300"
    problem_name = "a"
    language_name = "python"
    # prepare_test_environmentの返り値を上書き
    temp_source_path, temp_test_dir = tester.prepare_test_environment(contest_name, problem_name, language_name)
    temp_test_dir = Path(temp_test_dir)
    temp_source_path = Path(temp_source_path)
    # main.pyなどをtemp_test_dirにコピー
    for item in os.listdir(temp_test_dir.parent):
        pass  # 必要ならここでファイル確認
    temp_main = temp_test_dir.parent / "main.py"  # .temp/main.py を参照
    # デバッグ出力
    print(f"[DEBUG] temp_test_dir: {temp_test_dir}")
    print(f"[DEBUG] temp_test_dir.parent: {temp_test_dir.parent}")
    print(f"[DEBUG] temp_main: {temp_main}")
    print(f"[DEBUG] .temp dir contents: {list(temp_test_dir.parent.iterdir())}")
    if not temp_main.exists():
        pass
    assert temp_main.exists(), f"temp_test_dir.parent/main.pyが存在しません: {temp_main}"
    with open(temp_main, "r") as f:
        main_py_content = f.read()
    temp_in_files, in_files = tester.collect_test_cases(str(temp_test_dir), file_operator)
    temp_in_files = [Path(f) for f in temp_in_files]
    in_files = [Path(f) for f in in_files]
    for temp_in, orig_in in zip(temp_in_files, in_files):
        temp_out = temp_in.with_suffix('.out')
        orig_out = orig_in.with_suffix('.out')
        with open(temp_in, "r") as f:
            input_data = f.read()
        with open(orig_out, "r") as f:
            expected = f.read().strip()
        # docker runでテストケースを実行
        cmd = [
            "docker", "run", "--rm", "-i",
            "-v", f"{temp_test_dir.parent.absolute()}:/workspace",
            "-w", "/workspace",
            "python:3", "python3", "main.py"
        ]
        proc = subprocess.run(cmd, input=input_data, text=True, capture_output=True, cwd=os.getcwd())
        output = proc.stdout.strip()
        assert output == expected, f"input={temp_in}, output={output}, expected={expected}, stderr={proc.stderr}"
    # テスト後に一時ディレクトリを削除
    shutil.rmtree(".temp")
    shutil.rmtree("contest_current")

def test_command_test_run_test_e2e():
    file_operator = LocalFileOperator()
    file_manager = ContestFileManager(file_operator)
    tester = CommandTest(file_manager)
    contest_name = "abc300"
    problem_name = "a"
    language_name = "python"
    # E2Eでrun_testを実行
    asyncio.run(tester.run_test(contest_name, problem_name, language_name))
    # 例外が出なければOK（print出力はpytestのキャプチャ対象）

def test_command_open_e2e(tmp_path):
    import os
    import shutil
    from pathlib import Path
    # ホームディレクトリ配下に作業ディレクトリを作成
    work_dir = Path.home() / "cph_work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)
    # 必要なテンプレートを事前に作成
    os.makedirs("contest_template/python", exist_ok=True)
    with open("contest_template/python/main.py", "w", encoding="utf-8") as f:
        f.write("print('hello')\n")
    file_operator = LocalFileOperator(base_dir=work_dir)
    file_manager = ContestFileManager(file_operator)
    tester = CommandTest(file_manager)
    opener = MockOpener()
    command_open = CommandOpen(file_manager, opener)
    contest_name = "abc300"
    problem_name = "a"
    language_name = "python"
    test_dir = work_dir / "contest_current/test"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    try:
        asyncio.run(command_open.open(contest_name, problem_name, language_name))
    except Exception as e:
        pass
    assert test_dir.exists()
    in_files = [f for f in os.listdir(test_dir) if f.endswith('.in')]
    assert len(in_files) > 0, "テストケースがダウンロードされていない"
    with open(work_dir / "contest_current/info.json", "r", encoding="utf-8") as f:
        info = json.load(f)
    assert info["contest_name"] == contest_name
    assert info["problem_name"] == problem_name
    assert info["language_name"] == language_name
    assert len(opener.opened_urls) > 0
    assert contest_name in opener.opened_urls[0]
    # テスト後に作業ディレクトリを削除
    shutil.rmtree(work_dir)

def test_docker_hello_world():
    """Dockerコマンドとデーモンが正常に動作するかの超基本テスト"""
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "hello-world"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, f"docker run hello-world failed: {result.stderr}"
        assert "Hello from Docker!" in result.stdout
    except FileNotFoundError:
        assert False, "dockerコマンドが見つかりません"
    except Exception as e:
        assert False, f"Dockerの基本動作に失敗: {e}"

def test_docker_basic_commands():
    """docker info, version, images, ps などの基本コマンドが動作するか確認"""
    cmds = [
        ["docker", "info"],
        ["docker", "version"],
        ["docker", "images"],
        ["docker", "ps"]
    ]
    for cmd in cmds:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, f"{' '.join(cmd)} failed: {result.stderr}"
        except FileNotFoundError:
            assert False, f"dockerコマンドが見つかりません: {' '.join(cmd)}"
        except Exception as e:
            assert False, f"dockerコマンドの実行に失敗: {' '.join(cmd)}: {e}" 