
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

def submit_task(cmd: str, name: str):
    listen_heartbeat()
    TASKS.mkdir(exist_ok=True, parents=True)
    task_id = generate_task_id()
    task = {
        "id": task_id,
        "command": cmd,
        "created": timestamp(),
        "name": name
    }
    write_json(TASKS / f"{task_id}.json", task)
    print(f"[+] Submitted {task_id}")
        
from colorama import init, Fore, Style

def listen_heartbeat(ddl=10):
    for worker_file in STATUS.glob("*.json"):
        try:
            worker = read_json(worker_file)
        except Exception as e:
            print(f"[!] Error reading worker file {worker_file}: {e}")
            continue
        hb = worker.get("ts")
        hb = time.strptime(hb, "%Y-%m-%d %H:%M:%S")
        hb = time.mktime(hb)
        task_id = worker.get("task")

        if (hb is None or hb < time.time() - ddl) and worker.get("status") in ["running", "idle"]:
            print(f"[!] Worker {worker_file.stem} 心跳超时, 标记退出")

            if task_id:
                task_path = RUNNING / f"{task_id}.json"
                if task_path.exists():
                    task = read_json(task_path)
                    task["status"] = "failed"
                    task["ended"] = timestamp()
                    task["error"] = f"worker {worker_file.stem} heartbeat timeout"
                    write_json(FAILED / f"{task_id}.json", task)
                    task_path.unlink()

            worker["status"] = "abnormal"
            write_json(worker_file, worker)


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
            print(color + f"TaskName: {task.get('name', ''):<40} | {label}: {created} | {name} ")
            # print(color + f"{name} | {label}: {created} | TaskName: {task.get('name', '')[:20]}")
        if total > show_count:
            print(color + f"... and {total - show_count} more not shown\n")
        else:
            print()

    listen_heartbeat()

    print(Fore.CYAN + Style.BRIGHT + "=== Worker Status ===")
    for f in STATUS.glob("*.json"):
        data = read_json(f)
        taskid = data.get("task")
        taskname = RUNNING / f"{taskid}.json"
        if taskname.exists():
            taskname = read_json(taskname).get("name", "")
        else:
            taskname = str(taskid)
        print(Fore.GREEN + f"{f.name} | {taskname:<40} | {data}")
    print()

    list_tasks(RUNNING, Fore.YELLOW, "=== Running Tasks ===", reverse=True, max_count=recent_count)
    list_tasks(TASKS, Fore.MAGENTA, "=== Pending Tasks ===", reverse=False, max_count=recent_count)
    list_tasks(FINISHED, Fore.GREEN, "=== Finished Tasks ===", reverse=True, max_count=recent_count)
    list_tasks(FAILED, Fore.RED, "=== Failed Tasks ===")


def kill_task(task_id):
    listen_heartbeat()
    CONTROL.mkdir(exist_ok=True, parents=True)
    (CONTROL / f"kill-{task_id}").touch()
    print(f"[!] Kill signal sent for {task_id}")
    
def kill_worker(worker_id):
    listen_heartbeat()
    CONTROL.mkdir(exist_ok=True, parents=True)
    # find the worker file, find taskid (if it exists)
    # if taskid exists, kill the task
    # if taskid does not exist, do nothing
    worker_file = STATUS / f"{worker_id}.json"
    if worker_file.exists():
        worker = read_json(worker_file)
        task_id = worker.get("task")
        if task_id:
            kill_task(task_id)
        else:
            print(f"[!] Worker {worker_id} has no task, skipping")
    else:
        print(f"[!] Worker {worker_id} not found, skipping")

def cleanup_tasks(hours):
    listen_heartbeat()
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
    submit_parser.add_argument("--name", type=str, default="")

    status_parser = subparsers.add_parser("status")

    kill_parser = subparsers.add_parser("kill")
    kill_parser.add_argument("--task", required=True)

    kill_worker_parser = subparsers.add_parser("kill-worker")
    kill_worker_parser.add_argument("--worker", required=True)

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("--hours", type=int, required=True)

    args = parser.parse_args()

    for d in [TASKS, RUNNING, FINISHED, FAILED, STATUS, LOGS, LOCK, CONTROL]:
        d.mkdir(exist_ok=True, parents=True)

    if args.command == "submit":
        submit_task(args.cmd, args.name)
    elif args.command == "status":
        show_status()
    elif args.command == "kill":
        kill_task(args.task)
    elif args.command == "kill-worker":
        kill_worker(args.worker)
    elif args.command == "cleanup":
        cleanup_tasks(args.hours)

if __name__ == '__main__':
    main()