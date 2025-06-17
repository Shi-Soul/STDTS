
# ========== utils.py ==========

import os
import json
import time
from pathlib import Path

def atomic_lock(path: Path):
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return True
    except FileExistsError:
        return False

def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def write_json(path, data):
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def older_than(path: Path, seconds: int):
    return (time.time() - path.stat().st_mtime) > seconds