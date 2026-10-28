"""Explicit opt-in for the device-specific maintenance scripts preserved here."""
from pathlib import Path
import sys

def require_session_run():
    if not __debug__:
        raise SystemExit('历史脚本依赖断言校验，禁止通过 python -O 运行。')
    if '--run-session-script' not in sys.argv:
        raise SystemExit('这是固定设备路径/备份目录的历史脚本。先读 docs/maintenance.md；审阅后才可显式传入 --run-session-script。')
    if Path.cwd().resolve() != Path(__file__).resolve().parent:
        raise SystemExit('历史脚本只能在仓库根目录内运行。')
    sys.argv.remove('--run-session-script')
