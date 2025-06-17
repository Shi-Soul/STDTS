
# ========== server.py ==========

import argparse
import uuid
import shutil
from config import *
from utils import *
from operator import itemgetter

def submit_task(cmd: str, num: int):
    TASKS.mkdir(exist_ok=True, parents=True)
    for i in range(num):
        task_id = f"task-{str(uuid.uuid4())[:8]}"
        task = {
            "id": task_id,
            "command": cmd,
            "created": timestamp()
        }
        write_json(TASKS / f"{task_id}.json", task)
        print(f"[+] Submitted {task_id}")
from colorama import init, Fore, Style

init(autoreset=True)  # 自动重置颜色

def show_status(recent_finished_count=5):
    print(Fore.CYAN + Style.BRIGHT + "=== Worker Status ===")
    for f in STATUS.glob("*.json"):
        data = read_json(f)
        status_str = f"{f.name} :: {data}"
        print(Fore.GREEN + status_str)

    print("\n" + Fore.CYAN + Style.BRIGHT + "=== Running Tasks ===")
    for f in RUNNING.glob("*.json"):
        task = read_json(f)
        task_str = f"{f.name} | Command: {task.get('command', '')} | Created: {task.get('created', '')}"
        print(Fore.YELLOW + task_str)

    print("\n" + Fore.CYAN + Style.BRIGHT + "=== Pending Tasks ===")
    for f in TASKS.glob("*.json"):
        task = read_json(f)
        task_str = f"{f.name} | Command: {task.get('command', '')} | Created: {task.get('created', '')}"
        print(Fore.MAGENTA + task_str)

    print("\n" + Fore.CYAN + Style.BRIGHT + "=== Finished Tasks ===")
    finished_tasks = []
    for f in FINISHED.glob("*.json"):
        task = read_json(f)
        created = task.get("created", "")
        finished_tasks.append((f.name, created, task))

    # 按时间倒序排序，最近完成的排前面
    finished_tasks.sort(key=lambda x: x[1], reverse=True)

    total_finished = len(finished_tasks)
    print(Fore.GREEN + f"Total finished tasks: {total_finished}")

    if total_finished == 0:
        print(Fore.GREEN + "No finished tasks yet.")
        return

    # 显示最近几个任务
    for name, created, task in finished_tasks[:recent_finished_count]:
        finished_str = f"{name} | Created: {created} | Cmd: {task.get('command', '')}"
        print(Fore.GREEN + finished_str)

    if total_finished > recent_finished_count:
        print(Fore.GREEN + f"... and {total_finished - recent_finished_count} more finished tasks not shown")

    print("\n" + Fore.CYAN + Style.BRIGHT + "=== Failed Tasks ===")
    for f in FAILED.glob("*.json"):
        task = read_json(f)
        failed_str = f"{f.name} FAILED | Created: {task.get('created', '')}"
        print(Fore.RED + failed_str)


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