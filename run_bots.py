import subprocess
import sys
import time
import os
import asyncio
import config
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

bots_to_start = []

tworker_dir = os.path.join(BASE_DIR, 'tworker')
if config.BOT_ENABLED and os.path.exists(os.path.join(tworker_dir, 'run.py')):
    bots_to_start.append(tworker_dir)

nft_dir = os.path.join(BASE_DIR, 'tdrainer')
if os.path.exists(os.path.join(nft_dir, 'run.py')):
    bots_to_start.append(nft_dir)

stars_dir = os.path.join(BASE_DIR, 'tdrainer stars')
if os.path.exists(os.path.join(stars_dir, 'run.py')):
    bots_to_start.append(stars_dir)

processes = []

def start_all_bots():
    for bot_dir in bots_to_start:
        try:
            print(f'▶️  Запускаю бота из: {bot_dir}', flush=True)
            proc = subprocess.Popen([sys.executable, 'run.py'], cwd=bot_dir)
            processes.append(proc)
            time.sleep(3)
        except Exception as e:
            print(f'❌ Не удалось запустить из {bot_dir}: {e}', flush=True)
    print(f'✅ Запущено ботов: {len(processes)}', flush=True)

async def health(request):
    alive = [p for p in processes if p.poll() is None]
    return web.json_response({
        'status': 'ok',
        'bots_started': len(processes),
        'bots_alive': len(alive),
    })

async def start_health_server():
    port = int(os.getenv('PORT', '10000'))
    app = web.Application()
    app.router.add_get('/', health)
    app.router.add_get('/health', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f'🌐 Health server на 0.0.0.0:{port}', flush=True)
    return runner

async def main():
    start_all_bots()
    await start_health_server()

    # Мониторинг: если бот упал — перезапускаем
    while True:
        await asyncio.sleep(60)
        dead = [p for p in processes if p.poll() is not None]
        if dead:
            print(f'⚠️ Обнаружено упавших процессов: {len(dead)}. Перезапускаю...', flush=True)
            processes.clear()
            start_all_bots()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n🛑 Остановка...', flush=True)
        for proc in processes:
            proc.terminate()
