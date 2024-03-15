# Datei: log_helper.py
import logging
from logging.handlers import RotatingFileHandler

import datetime

# Aktualisierte Farbcodes
class LogColors:
    CRITICAL = '\033[0;31m'  # Rot
    SUCCESS = '\033[0;32m'   # Grün
    ERROR = '\033[0;33m'     # Gelb
    SYSTEM = '\033[0;34m'    # Blau
    INFO = '\033[0;35m'      # Lila
    USER_ACTION = '\033[0;36m' # Cyan
    NORMAL = '\033[0;37m'    # Weiß


def create_logger(type):
    # Logger erstellen
    logger = logging.getLogger(type)
    logger.setLevel(logging.DEBUG)

    return logger

def create(type):
    logger = create_logger(type)

    # Funktion zum Loggen mit Farben
    def log(message, level="NORMAL"):
        color = {
            "CRITICAL": LogColors.CRITICAL,
            "SUCCESS": LogColors.SUCCESS,
            "ERROR": LogColors.ERROR,
            "SYSTEM": LogColors.SYSTEM,
            "INFO": LogColors.INFO,
            "USER_ACTION": LogColors.USER_ACTION,
            "NORMAL": LogColors.NORMAL
        }.get(level, LogColors.NORMAL)

        # clear the handler list
        logger.handlers.clear()

        #get date in format DD-MM-YYYY
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        log_file_path = f"logs/{date}.log"

        # Festlegen des Formats für den Logger
        file_handler = RotatingFileHandler(log_file_path, maxBytes=5000000, backupCount=2)
        console_handler = logging.StreamHandler()
        if level == "NORMAL":
            file_handler.setFormatter(logging.Formatter(f"[%(asctime)s] [{type}] %(message)s", datefmt='%H:%M:%S'))
            console_handler.setFormatter(logging.Formatter(f"{color}[%(asctime)s] [{type}] %(message)s", datefmt='%H:%M:%S'))
        else:
            file_handler.setFormatter(logging.Formatter(f"[%(asctime)s] [{type}/{level}] %(message)s", datefmt='%H:%M:%S'))
            console_handler.setFormatter(logging.Formatter(f"{color}[%(asctime)s] [{type}/{level}] %(message)s", datefmt='%H:%M:%S'))
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Log-Nachricht senden
        getattr(logger, level.lower(), logger.info)(message)

    return log

