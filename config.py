
# ========== config.py ==========
# 用于定义常量路径

import os
from pathlib import Path

QUEUE_ROOT = Path(os.environ.get("TASK_QUEUE_ROOT", "/home/bai/STDTS/task_queue"))

TASKS = QUEUE_ROOT / "tasks"
RUNNING = QUEUE_ROOT / "running"
FINISHED = QUEUE_ROOT / "finished"
FAILED = QUEUE_ROOT / "failed"
STATUS = QUEUE_ROOT / "status"
LOGS = QUEUE_ROOT / "logs"
LOCK = QUEUE_ROOT / "lock"
CONTROL = QUEUE_ROOT / "control"