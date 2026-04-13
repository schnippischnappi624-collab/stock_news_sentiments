import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def test_install_daily_cron_installs_eu_and_us_jobs_by_default(tmp_path: Path) -> None:
    root = tmp_path
    script_source = Path("stock_news/scripts/install_daily_cron.sh").read_text(encoding="utf-8")
    script_path = root / "stock_news" / "scripts" / "install_daily_cron.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    _write_executable(script_path, script_source)

    bin_dir = root / "bin"
    bin_dir.mkdir()
    crontab_store = root / "crontab.txt"
    crontab_store.write_text(
        "CRON_TZ=Europe/Vienna\n15 11 * * * cd /old/root && /bin/bash /old/root/stock_news/scripts/run_daily_and_push.sh\n",
        encoding="utf-8",
    )

    _write_executable(
        bin_dir / "crontab",
        """#!/usr/bin/env bash
if [[ "${1:-}" == "-l" ]]; then
  cat "$TEST_CRONTAB"
elif [[ "${1:-}" == "-" ]]; then
  cat > "$TEST_CRONTAB"
else
  exit 2
fi
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["TEST_CRONTAB"] = str(crontab_store)

    subprocess.run([str(script_path)], cwd=str(root), env=env, check=True)

    installed = crontab_store.read_text(encoding="utf-8")
    assert "0 6 * * *" in installed
    assert "run_daily_and_push.sh EU" in installed
    assert "15 11 * * *" in installed
    assert "run_daily_and_push.sh US" in installed
    assert "/old/root/stock_news/scripts/run_daily_and_push.sh" not in installed


def test_install_daily_cron_installs_single_region_job(tmp_path: Path) -> None:
    root = tmp_path
    script_source = Path("stock_news/scripts/install_daily_cron.sh").read_text(encoding="utf-8")
    script_path = root / "stock_news" / "scripts" / "install_daily_cron.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    _write_executable(script_path, script_source)

    bin_dir = root / "bin"
    bin_dir.mkdir()
    crontab_store = root / "crontab.txt"
    crontab_store.write_text(
        "CRON_TZ=Europe/Vienna\n15 11 * * * cd /existing/root && /bin/bash /existing/root/stock_news/scripts/run_daily_and_push.sh US\n",
        encoding="utf-8",
    )

    _write_executable(
        bin_dir / "crontab",
        """#!/usr/bin/env bash
if [[ "${1:-}" == "-l" ]]; then
  cat "$TEST_CRONTAB"
elif [[ "${1:-}" == "-" ]]; then
  cat > "$TEST_CRONTAB"
else
  exit 2
fi
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["TEST_CRONTAB"] = str(crontab_store)

    subprocess.run([str(script_path), "EU"], cwd=str(root), env=env, check=True)

    installed = crontab_store.read_text(encoding="utf-8")
    assert "0 6 * * *" in installed
    assert "run_daily_and_push.sh EU" in installed
    assert "run_daily_and_push.sh US" in installed
