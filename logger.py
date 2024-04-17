import logging
import sys
from colorama import init, Fore, Style

init(autoreset=True)


class CustomFormatter(logging.Formatter):
    def format(self, record):
        levelno = record.levelno
        if levelno >= logging.CRITICAL:
            color = Fore.RED + Style.BRIGHT
        elif levelno >= logging.ERROR:
            color = Fore.RED
        elif levelno >= logging.WARNING:
            color = Fore.YELLOW + Style.DIM
        elif levelno >= logging.INFO:
            color = Fore.GREEN
        else:
            color = Fore.WHITE

        time_str = self.formatTime(record, "%H:%M:%S")
        filename_func = f"{record.filename}->{record.funcName}()"

        # Выравнивание
        time_str = f"{time_str:<8}"  # 8 символов для времени
        filename_func = f"{filename_func:<30}"  # 30 символов для имени файла и функции

        return f"{Fore.YELLOW}{time_str} | {Fore.WHITE}{filename_func} | {color}{record.getMessage()}"


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(CustomFormatter())

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)

logger = root_logger
