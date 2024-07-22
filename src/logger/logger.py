import logging
from threading import Lock
from typing import Callable, Optional, Dict, Union

from PySide6.QtCore import QObject, Signal


class LogEmitter(QObject):
    log_signal = Signal(str)


class Logger:
    _instances: Dict[str, 'Logger'] = {}
    _lock = Lock()
    _log_emitter = LogEmitter()

    def __new__(cls, function_name: str, *args, **kwargs):
        with cls._lock:
            if function_name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[function_name] = instance
            return cls._instances[function_name]

    def __init__(
            self,
            function_name: str,
            log_level: int = logging.INFO,
    ):
        """
        Initializes the Logger.

        Args:
            function_name (str): The name of the function or module.
            log_level (int): The log level (e.g., logging.DEBUG, logging.INFO).
            emit_func (Optional[Callable]): If provided, log messages will be emitted to this function.
                                            Can accept either (msg) or (msg, color).
        """
        if hasattr(self, "initialized") and self.initialized:
            return
        self.initialized: bool = True

        self.logger = logging.getLogger(function_name)
        self.logger.setLevel(log_level)

        if not self.logger.hasHandlers():
            formatter = logging.Formatter("%(message)s")

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            class SignalHandler(logging.Handler):
                def emit(self_handler, record):
                    log_entry = self_handler.format(record)
                    Logger._log_emitter.log_signal.emit(log_entry)

            signal_handler = SignalHandler()
            signal_handler.setFormatter(formatter)
            self.logger.addHandler(signal_handler)

    def _log(self, level: int, message: str):
        """
        Logs a message with color coding.

        Args:
            level (int): The log level.
            message (str): The message to log.
        """
        getattr(self.logger, logging.getLevelName(level).lower())(message)

    def debug(self, message: str):
        """Logs a debug message."""
        self._log(logging.DEBUG, message)

    def info(self, message: str):
        """Logs an info message."""
        self._log(logging.INFO, message)

    def warning(self, message: str):
        """Logs a warning message."""
        self._log(logging.WARNING, message)

    def error(self, message: str):
        """Logs an error message."""
        self._log(logging.ERROR, message)

    def critical(self, message: str):
        """Logs a critical message."""
        self._log(logging.CRITICAL, message)

    def exception(self, message: str):
        """Logs an exception message with traceback."""
        self.logger.exception(message)

    @classmethod
    def connect_log_signal(cls, slot: Callable[[str], None]):
        """
        Connects the log signal to a slot function.

        Args:
            slot (Callable[[str], None]): The function to call when a log is emitted.
        """
        cls._log_emitter.log_signal.connect(slot)


logger = Logger(__name__)
