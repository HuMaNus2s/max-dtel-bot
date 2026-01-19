import logging
import sys

def setup_logging(level=logging.INFO, log_file="app.log"):
    """
    Инициализация корневого логгера
    #### Args:
    - level: Уровень логгирования (logging.INFO)
    - log_file: Куда будет записывать лог (_DEFAULT_ _app.log_)
    """
    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return root