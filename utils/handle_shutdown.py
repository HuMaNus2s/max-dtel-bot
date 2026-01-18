import asyncio

def handle_shutdown(loop):
    """
    Завершает асинхронный цикл событий при остановке бота.
    
    #### Args:
        loop: Текущий asyncio event loop (asyncio.AbstractEventLoop)
    
    Что делает:
    - Отменяет все оставшиеся задачи
    - Останавливает цикл
    - Завершает асинхронные генераторы
    - Закрывает event loop
    """
    tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task(loop)]
    for task in tasks:
        task.cancel()
    loop.stop()
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()