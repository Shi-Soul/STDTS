# A Shared Task Queue for Distributed Computing


```bash
# === 项目结构说明 ===
# 共享目录结构:
# /task_queue/
#   tasks/      -> 待执行任务
#   running/    -> 运行中的任务
#   finished/   -> 成功完成的任务
#   failed/     -> 执行失败的任务
#   status/     -> 每张卡一个JSON状态文件
#   logs/       -> 每个任务一个日志输出文件
#   lock/       -> 原子锁目录
#   control/    -> 控制命令 (如 kill task)
```

```bash
python server.py submit --cmd "echo 123; sleep 3; echo 456" --name "test"
python server.py status
python server.py kill --task task-xxxx
```

```bash
python server_monitor.py --cleanup-interval 1800 --cleanup-hours 12 --status-interval 120
```

```bash
python worker.py --gpu-id 0 --worker-id node01-0 #--save-log
```