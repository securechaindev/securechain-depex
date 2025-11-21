from logging import INFO, Formatter, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LoggerManager:
    instance: LoggerManager | None = None
    initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(
        self,
        log_file: str = "app/logs/errors.log",
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:
        if self.initialized:
            return

        self.logger = getLogger("securechain")
        self.logger.setLevel(INFO)
        self.logger.propagate = False

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        formatter = Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

        self.initialized = True

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

logger = LoggerManager()
