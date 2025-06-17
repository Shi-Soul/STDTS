
# ========== worker.py ==========

import argparse
import subprocess
import signal
from threading import Thread

from config import *
from utils import *
def run_task(task, worker_id, gpu_id, save_log):
    import signal
    from threading import Thread
    import subprocess

    task_id = task["id"]
    log_path = LOGS / f"{task_id}.log"

    if (CONTROL / f"kill-{task_id}").exists():
        print(f"[!] {task_id} skipped due to existing kill signal.")
        return

    print(f"[+] Running {task_id}")

    log_file = open(log_path, "w") if save_log else None

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
            if save_log:
                log_file.write(line)
                log_file.flush()

    t = Thread(target=printer)
    t.start()

    try:
        while proc.poll() is None:
            if (CONTROL / f"kill-{task_id}").exists():
                msg = f"[!] {task_id} received kill signal, terminating..."
                print(msg)
                if save_log:
                    log_file.write(msg)
                    log_file.flush()
                proc.terminate()
                break
            time.sleep(2)
    except KeyboardInterrupt:
        msg = f"[!] KeyboardInterrupt: Terminating task {task_id}"
        print(msg)
        if save_log:
            log_file.write(msg)
            log_file.flush()
        proc.terminate()

    t.join()
    code = proc.wait()

    if save_log:
        log_file.close()

    dest = FINISHED if code == 0 else FAILED
    write_json(dest / f"{task_id}.json", task)
    (RUNNING / f"{task_id}.json").unlink(missing_ok=True)
    (TASKS / f"{task_id}.json").unlink(missing_ok=True)
    print(f"[+] {task_id} finished with code {code}")

def worker_loop(worker_id, gpu_id, save_log):
    worker_status_path = STATUS / f"{worker_id}.json"
    worker_status = {
                    "gpu": gpu_id,
                    "status": "idle",
                    "ts": timestamp()
                }
    print(f"[+] Starting worker {worker_id} (GPU {gpu_id}, save_log={save_log})")
    try:
        while True:
            try:
                # 写入空闲状态
                worker_status["status"] = "idle"
                worker_status["ts"] = timestamp()
                write_json(worker_status_path, worker_status)

                # 查找按创建时间排序的任务
                task_files = sorted(TASKS.glob("*.json"), key=lambda f: read_json(f).get("created", ""))
                for f in task_files:
                    task = read_json(f)

                    lock_path = LOCK / f"{f.stem}.lock"
                    if not atomic_lock(lock_path):
                        continue

                    write_json(RUNNING / f.name, task)
                    f.unlink()
                    worker_status["status"] = "running"
                    worker_status["task"] = task["id"]
                    worker_status["ts"] = timestamp()
                    write_json(worker_status_path, worker_status)

                    run_task(task, worker_id, gpu_id, save_log)
                    break

                time.sleep(5)

            except KeyboardInterrupt:
                print(f"[!] Worker {worker_id} received keyboard interrupt")
                break

            except Exception as e:
                print(f"[!] Worker {worker_id} unexpected error: {e}")
                time.sleep(5)

    finally:
        print(f"[!] Worker {worker_id} exiting...")
        worker_status["status"] = "exited"
        worker_status["ts"] = timestamp()
        write_json(worker_status_path, worker_status)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu-id", type=int, required=True)
    parser.add_argument("--worker-id", type=str, required=True)
    parser.add_argument("--save-log", action="store_true", help="Save log to file")
    args = parser.parse_args()

    worker_loop(args.worker_id, args.gpu_id, args.save_log)

if __name__ == '__main__':
    main()