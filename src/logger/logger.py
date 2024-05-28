import logging
from typing import Callable, Optional
from threading import Lock


class Logger:
    _instances = {}
    _lock = Lock()

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
        emit_func: Optional[Callable[[str], None]] = None,
    ):
        """
        Initializes the Logger.

        Args:
            function_name (str): The name of the function or module.
            log_level (int): The log level (e.g., logging.DEBUG, logging.INFO).
            emit_func (Optional[Callable[[str], None]]): If provided, log messages will be emitted to this function.
        """
        if hasattr(self, "initialized") and self.initialized:
            return
        self.initialized = True

        self.logger = logging.getLogger(function_name)
        self.logger.setLevel(log_level)

        # Prevent adding multiple handlers to the same logger
        if not self.logger.hasHandlers():
            # Log format
            formatter = logging.Formatter("%(message)s")

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # Optional GUI handler
            if emit_func:

                class GuiHandler(logging.Handler):
                    def emit(self, record):
                        log_entry = self.format(record)
                        emit_func(log_entry)

                gui_handler = GuiHandler()
                gui_handler.setFormatter(formatter)
                self.logger.addHandler(gui_handler)

    def info(self, message: str):
        """Logs an info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Logs a warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Logs an error message."""
        self.logger.error(message)

    def exception(self, message: str):
        """Logs an exception message with traceback."""
        self.logger.exception(message)

    def debug(self, message: str):
        """Logs a debug message."""
        self.logger.debug(message)
