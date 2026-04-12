import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def test_wrapper_script_skips_when_no_changes(tmp_path: Path) -> None:
    root = tmp_path
    script_source = Path("stock_news/scripts/run_daily_and_push.sh").read_text(encoding="utf-8")
    script_path = root / "stock_news" / "scripts" / "run_daily_and_push.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    _write_executable(script_path, script_source)

    bin_dir = root / "bin"
    bin_dir.mkdir()
    log_path = root / "cmd.log"

    _write_executable(
        bin_dir / "poetry",
        """#!/usr/bin/env bash
echo "poetry $*" >> "$TEST_LOG"
exit 0
""",
    )
    _write_executable(
        bin_dir / "git",
        """#!/usr/bin/env bash
case "$1" in
  status) exit 0 ;;
  add) echo "git add" >> "$TEST_LOG"; exit 0 ;;
  diff) exit 0 ;;
  commit) echo "git commit" >> "$TEST_LOG"; exit 0 ;;
  push) echo "git push" >> "$TEST_LOG"; exit 0 ;;
esac
exit 0
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["TEST_LOG"] = str(log_path)

    subprocess.run([str(script_path)], cwd=str(root), env=env, check=True)

    log = log_path.read_text(encoding="utf-8")
    assert "poetry run stock-news daily-run" in log
    assert "git commit" not in log
    assert "git push" not in log


def test_wrapper_script_commits_when_generated_artifacts_change(tmp_path: Path) -> None:
    root = tmp_path
    script_source = Path("stock_news/scripts/run_daily_and_push.sh").read_text(encoding="utf-8")
    script_path = root / "stock_news" / "scripts" / "run_daily_and_push.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    _write_executable(script_path, script_source)

    bin_dir = root / "bin"
    bin_dir.mkdir()
    log_path = root / "cmd.log"

    _write_executable(
        bin_dir / "poetry",
        """#!/usr/bin/env bash
echo "poetry $*" >> "$TEST_LOG"
exit 0
""",
    )
    _write_executable(
        bin_dir / "git",
        """#!/usr/bin/env bash
case "$1" in
  status) echo " M latest/dashboard.md"; exit 0 ;;
  add) echo "git add" >> "$TEST_LOG"; exit 0 ;;
  diff) exit 1 ;;
  commit) echo "git commit" >> "$TEST_LOG"; exit 0 ;;
  push) echo "git push" >> "$TEST_LOG"; exit 0 ;;
esac
exit 0
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["TEST_LOG"] = str(log_path)

    subprocess.run([str(script_path)], cwd=str(root), env=env, check=True)

    log = log_path.read_text(encoding="utf-8")
    assert "git add" in log
    assert "git commit" in log
    assert "git push" in log
