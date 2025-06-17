
# ========== worker.py ==========

import argparse
import subprocess
import signal
from threading import Thread

from config import *
from utils import *


def run_task(task, worker_id, gpu_id):
    task_id = task["id"]
    log_path = LOGS / f"{task_id}.log"

    print(f"[+] Running {task_id} on GPU {gpu_id}")
    with open(log_path, "w") as f:
        proc = subprocess.Popen(
            task["command"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={**os.environ, "CUDA_VISIBLE_DEVICES": str(gpu_id)}
        )

        def printer():
            for line in proc.stdout:
                line = line.decode()
                print(f"[{task_id}] {line}", end="")
                f.write(line)
                f.flush()

        t = Thread(target=printer)
        t.start()

        while proc.poll() is None:
            if (CONTROL / f"kill-{task_id}").exists():
                proc.terminate()
                print(f"[!] {task_id} received kill signal")
                break
            time.sleep(2)

        t.join()
        code = proc.returncode

    dest = FINISHED if code == 0 else FAILED
    write_json(dest / f"{task_id}.json", task)
    (RUNNING / f"{task_id}.json").unlink(missing_ok=True)
    (TASKS / f"{task_id}.json").unlink(missing_ok=True)
    print(f"[+] {task_id} finished with code {code}")


def worker_loop(worker_id, gpu_id):
    while True:
        write_json(STATUS / f"{worker_id}.json", {"gpu": gpu_id, "status": "idle", "ts": timestamp()})
        for f in sorted(TASKS.glob("*.json")):
            lock_path = LOCK / f"{f.stem}.lock"
            if not atomic_lock(lock_path):
                continue

            task = read_json(f)
            write_json(RUNNING / f.name, task)
            write_json(STATUS / f"{worker_id}.json", {"gpu": gpu_id, "status": "running", "task": task["id"], "ts": timestamp()})
            run_task(task, worker_id, gpu_id)
            break
        time.sleep(5)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu-id", type=int, required=True)
    parser.add_argument("--worker-id", type=str, required=True)
    args = parser.parse_args()

    worker_loop(args.worker_id, args.gpu_id)

if __name__ == '__main__':
    main()
