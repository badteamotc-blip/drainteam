import subprocess
import sys
import time
import config

bots_to_start = []

if config.BOT_ENABLED:
    bots_to_start.append([sys.executable, 'tworker/run.py'])

# Drainer processes are not started automatically. DRAIN_TARGET_ID is intentionally
# empty and asset-transfer functionality is not configured.

processes = []
for bot_cmd in bots_to_start:
    try:
        proc = subprocess.Popen(bot_cmd)
        processes.append(proc)
        time.sleep(3)
    except Exception as e:
        print(f'Failed to start {bot_cmd}: {e}')

try:
    while True:
        time.sleep(60)
        processes = [p for p in processes if p.poll() is None]
except KeyboardInterrupt:
    for proc in processes:
        proc.terminate()
