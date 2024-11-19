import logging

uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.getLevelName(logging.DEBUG))

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_file_handler = logging.FileHandler("errors.log")
error_file_handler.setLevel(logging.DEBUG)
error_file_handler.setFormatter(formatter)
logger.addHandler(error_file_handler)
