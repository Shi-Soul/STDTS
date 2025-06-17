


```bash
python server.py submit --cmd "echo 123; sleep 3; echo 456" --num 4
python server.py status
python server.py kill --task task-xxxx
```

```bash
python server_monitor.py --cleanup-interval 1800 --cleanup-hours 12 --status-interval 120
```

```bash
python worker.py --gpu-id 0 --worker-id node01-0 #--save-log
```