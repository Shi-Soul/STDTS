import time
import signal
import argparse
from math import ceil
from config import *
from utils import *
from server import cleanup_tasks, show_status

STOP = False

def signal_handler(signum, frame):
    global STOP
    print("[!] Received stop signal, exiting monitor...")
    STOP = True

def monitor_loop(cleanup_interval, cleanup_hours, status_interval):
    last_cleanup = 0
    while not STOP:
        now = time.time()

        print("=" * 100)
        if now - last_cleanup > cleanup_interval:
            print(f"[Monitor] Running cleanup for tasks older than {cleanup_hours} hours...")
            cleanup_tasks(cleanup_hours)
            last_cleanup = now

        print(f"[Monitor] Current status at {timestamp()}:")
        show_status()

        for i in range(ceil(status_interval)):
            if STOP:
                break
            dt = status_interval - i
            time.sleep(dt)

def main():
    parser = argparse.ArgumentParser(description="Distributed Task System Server Monitor")
    parser.add_argument(
        "--cleanup-interval",
        type=int,
        default=3600,
        help="Cleanup interval in seconds (default: 3600s = 1h)"
    )
    parser.add_argument(
        "--cleanup-hours",
        type=int,
        default=24,
        help="Cleanup threshold: tasks older than this hours will be removed (default: 24h)"
    )
    parser.add_argument(
        "--status-interval",
        type=float,
        default=300,
        help="Status print interval in seconds (default: 300s = 5min)"
    )

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("[Monitor] Starting server monitor...")
    monitor_loop(args.cleanup_interval, args.cleanup_hours, args.status_interval)

if __name__ == "__main__":
    main()
