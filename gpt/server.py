
# ========== server.py ==========

import argparse
import uuid
import shutil
from config import *
from utils import *

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

def show_status():
    print("=== Worker Status ===")
    for f in STATUS.glob("*.json"):
        data = read_json(f)
        print(f.name, "::", data)

    print("\n=== Running Tasks ===")
    for f in RUNNING.glob("*.json"):
        task = read_json(f)
        print(f.name, task)

    print("\n=== Pending Tasks ===")
    for f in TASKS.glob("*.json"):
        task = read_json(f)
        print(f.name, task)

    print("\n=== Finished Tasks ===")
    for f in FINISHED.glob("*.json"):
        task = read_json(f)
        print(f.name, "FINISHED", "created:", task.get("created"))

    print("\n=== Failed Tasks ===")
    for f in FAILED.glob("*.json"):
        task = read_json(f)
        print(f.name, "FAILED", "created:", task.get("created"))

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
    submit_parser.add_argument("--num", type=int, required=True)

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