import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

BOTS = [
    BASE_DIR / "tworker" / "run.py",
    BASE_DIR / "tdrainer" / "run.py",
    BASE_DIR / "tdrainer stars" / "run.py",
]

processes = []

def start_bot(path):
    if not path.is_file():
        print(f"[ERROR] Не найден файл: {path}")
        return None

    print(f"[START] {path}")
    return subprocess.Popen([sys.executable, str(path)], cwd=str(BASE_DIR))

try:
    for bot in BOTS:
        proc = start_bot(bot)
        if proc is not None:
            processes.append(proc)
        time.sleep(3)

    print(f"[INFO] Запущено процессов: {len(processes)}/{len(BOTS)}")
    print("[INFO] Для остановки нажмите Ctrl+C.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[INFO] Остановка всех ботов...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()

    for proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    print("[INFO] Все процессы остановлены.")
