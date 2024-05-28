import logging
from typing import Callable, Optional


class Logger:
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
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def exception(self, message: str):
        self.logger.exception(message)

    def debug(self, message: str):
        self.logger.debug(message)


logger = Logger(__name__)
