
# ========== server.py ==========

import argparse
import uuid
import shutil
from config import *
from utils import *
from operator import itemgetter
import uuid
import time

def base36_encode(number: int) -> str:
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    result = ''
    while number:
        number, i = divmod(number, 36)
        result = chars[i] + result
    return result or '0'

def generate_task_id():
    ts = int(time.time()*100)  # 当前时间戳（秒）
    ts_b36 = base36_encode(ts)[-4:]  # 转成base36，缩短长度
    rand = str(uuid.uuid4())[:4]  # 简短随机字符串
    return f"task-{ts_b36}{rand}"

def submit_task(cmd: str, num: int):
    TASKS.mkdir(exist_ok=True, parents=True)
    for i in range(num):
        task_id = generate_task_id()
        task = {
            "id": task_id,
            "command": cmd,
            "created": timestamp()
        }
        write_json(TASKS / f"{task_id}.json", task)
        print(f"[+] Submitted {task_id}")
        
from colorama import init, Fore, Style

init(autoreset=True)  # 自动重置颜色
def show_status(recent_count=5):
    def list_tasks(folder, color, title, reverse=False, label="Created", max_count=None):
        tasks = []
        for f in folder.glob("*.json"):
            task = read_json(f)
            created = task.get("created", "")
            tasks.append((f.name, created, task))
        tasks.sort(key=lambda x: x[1], reverse=reverse)

        total = len(tasks)
        print(color + f"{title} ({total})")
        if total == 0:
            print(color + "No tasks.\n")
            return

        show_count = total if max_count is None else min(total, max_count)
        for name, created, task in tasks[:show_count]:
            print(color + f"{name} | {label}: {created} | Cmd: {task.get('command', '')}")
        if total > show_count:
            print(color + f"... and {total - show_count} more not shown\n")
        else:
            print()

    print(Fore.CYAN + Style.BRIGHT + "=== Worker Status ===")
    for f in STATUS.glob("*.json"):
        data = read_json(f)
        print(Fore.GREEN + f"{f.name} :: {data}")
    print()

    list_tasks(RUNNING, Fore.YELLOW, "=== Running Tasks ===")
    list_tasks(TASKS, Fore.MAGENTA, "=== Pending Tasks ===", reverse=False, max_count=recent_count)
    list_tasks(FINISHED, Fore.GREEN, "=== Finished Tasks ===", reverse=True, max_count=recent_count)
    list_tasks(FAILED, Fore.RED, "=== Failed Tasks ===")


def kill_task(task_id):
    CONTROL.mkdir(exist_ok=True, parents=True)
    (CONTROL / f"kill-{task_id}").touch()
    print(f"[!] Kill signal sent for {task_id}")
    
def cleanup_tasks(hours):
    seconds = hours * 3600
    for folder in [FINISHED, FAILED]:
        for f in folder.glob("*.json"):
            if older_than(f, seconds):
                task_id = f.stem
                print(f"[~] Removing {task_id} from {folder.name}")
                f.unlink()

                log_file = LOGS / f"{task_id}.log"
                if log_file.exists():
                    log_file.unlink()

                lock_file = LOCK / f"{task_id}.lock"
                if lock_file.exists():
                    lock_file.unlink()


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("--cmd", required=True)
    submit_parser.add_argument("--num", type=int, default=1)

    status_parser = subparsers.add_parser("status")

    kill_parser = subparsers.add_parser("kill")
    kill_parser.add_argument("--task", required=True)

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("--hours", type=int, required=True)

    args = parser.parse_args()

    for d in [TASKS, RUNNING, FINISHED, FAILED, STATUS, LOGS, LOCK, CONTROL]:
        d.mkdir(exist_ok=True, parents=True)

    if args.command == "submit":
        submit_task(args.cmd, args.num)
    elif args.command == "status":
        show_status()
    elif args.command == "kill":
        kill_task(args.task)
    elif args.command == "cleanup":
        cleanup_tasks(args.hours)

if __name__ == '__main__':
    main()