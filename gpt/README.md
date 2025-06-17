


```bash
python server.py submit --cmd "python train.py --cfg cfg.yaml" --num 4
python server.py status
python server.py kill --task task-xxxx

```

```bash
python worker.py --gpu-id 0 --worker-id node01-0 --save-log
```