import logging
from logging.handlers import RotatingFileHandler

uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

rotating_handler = RotatingFileHandler("errors.log", maxBytes=5 * 1024 * 1024, backupCount=3)
rotating_handler.setLevel(logging.DEBUG)
rotating_handler.setFormatter(formatter)

logger.addHandler(rotating_handler)
