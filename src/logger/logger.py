import logging
from threading import Lock
from typing import Callable, Dict, Type, TypeVar

from PySide6.QtCore import QObject, Signal

T = TypeVar('T', bound='Logger')


class LogEmitter(QObject):
    log_signal = Signal(str)


class Logger:
    _instances: Dict[str, 'Logger'] = {}
    _lock = Lock()
    _log_emitter = LogEmitter()
    _ui_logging_enabled = True

    def __new__(cls: Type[T], function_name: str, *args, **kwargs) -> T:
        """
        Create a new instance of the class if it doesn't already exist for the given function name.

        Args:
            cls (type): The class object.
            function_name (str): The name of the function.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            object: The instance of the class.

        """
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
        """
        if hasattr(self, "initialized") and self.initialized:
            return
        self.initialized: bool = True

        self.function_name = function_name
        self.log_level = log_level

        self.console_logger = logging.getLogger(f"{function_name}_console")
        self.ui_logger = logging.getLogger(f"{function_name}_ui")

        self.console_logger.setLevel(log_level)
        self.ui_logger.setLevel(log_level)

        self._setup_console_logger()
        self._setup_ui_logger()

    def _setup_console_logger(self):
        """
        Set up the console logger for the application.

        This function checks if the console logger has any handlers. If not, it creates a formatter
        object with the message format "%(message)s" and a console handler object. The console
        handler is then added to the console logger.

        Returns:
            None
        """
        if not self.console_logger.hasHandlers():
            formatter = logging.Formatter("%(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.console_logger.addHandler(console_handler)

    def _setup_ui_logger(self):
        """
        Set up the UI logger for the application.

        This function checks if the UI logger has any handlers. If not, it creates a formatter
        object with the message format "%(message)s" and a SignalHandler class. The SignalHandler
        class emits log entries if UI logging is enabled.

        Returns:
            None
        """
        if not self.ui_logger.hasHandlers():
            formatter = logging.Formatter("%(message)s")

            class SignalHandler(logging.Handler):
                def emit(self, record):
                    """
                    Emits log entries if UI logging is enabled.
                    Parameters:
                        record: The log record to emit.
                    Returns:
                        None
                    """
                    log_entry = self.format(record)
                    if Logger._ui_logging_enabled:
                        Logger._log_emitter.log_signal.emit(log_entry)

            signal_handler = SignalHandler()
            signal_handler.setFormatter(formatter)
            self.ui_logger.addHandler(signal_handler)

    def _log(self, level: int, message: str):
        """
        Logs a message with color coding.

        Args:
            level (int): The log level.
            message (str): The message to log.
        """
        log_method = logging.getLevelName(level).lower()
        getattr(self.console_logger, log_method)(message)
        getattr(self.ui_logger, log_method)(message)

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
        self.console_logger.exception(message)
        self.ui_logger.exception(message)

    @classmethod
    def connect_log_signal(cls, slot: Callable[[str], None]):
        """
        Connects the log signal to a slot function.

        Args:
            slot (Callable[[str], None]): The function to call when a log is emitted.
        """
        cls._log_emitter.log_signal.connect(slot)

    @classmethod
    def set_ui_logging(cls, enabled: bool):
        """
        Sets the UI logging status based on the given boolean value.

        Args:
            cls: The class itself.
            enabled (bool): A boolean value indicating whether UI logging should be enabled.
        """
        cls._ui_logging_enabled = enabled

    @classmethod
    def set_console_logging(cls, enabled: bool):
        """
        Set the console logging for all instances of the class.

        Args:
            enabled (bool): True to enable console logging, False to disable.

        This class method iterates over all instances of the class and either
        sets up the console logger or clears the console logger's handlers
        depending on the value of the `enabled` parameter.

        Returns:
            None
        """
        for log in cls._instances.values():
            if enabled:
                log._setup_console_logger()
            else:
                log.console_logger.handlers.clear()


logger = Logger(__name__)
