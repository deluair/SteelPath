"""
Logger configuration for the SteelPath simulation platform.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
# from ..config.settings import LoggingConfig # Assuming config structure

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

def setup_logging(log_level_str: str = DEFAULT_LOG_LEVEL, 
                  log_file: str = None, 
                  log_format: str = DEFAULT_LOG_FORMAT,
                  max_bytes: int = 10*1024*1024, # 10 MB
                  backup_count: int = 5):
    """
    Configures the root logger for the application.

    Args:
        log_level_str (str): The logging level (e.g., 'DEBUG', 'INFO').
        log_file (str, optional): Path to the log file. If None, logs to stdout.
        log_format (str): The format string for log messages.
        max_bytes (int): Maximum size for a log file before rotation.
        backup_count (int): Number of backup log files to keep.
    """
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicate logs if called multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(log_format)

    if log_file:
        # File handler with rotation
        try:
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logging.info(f"Logging to file: {log_file} at level {log_level_str}")
        except Exception as e:
            # Fallback to console if file logging fails
            print(f"Error setting up file logger at {log_file}: {e}. Falling back to console logging.", file=sys.stderr)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            logging.info(f"Logging to console at level {log_level_str} due to file logger error.")
    else:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        logging.info(f"Logging to console at level {log_level_str}")

# Example of using this setup with a config object (conceptual)
# def setup_logging_from_config(config: LoggingConfig):
#     setup_logging(log_level_str=config.level, log_file=config.log_file)

if __name__ == '__main__':
    # Example usage:
    setup_logging(log_level_str="DEBUG", log_file="temp_app.log")
    logging.debug("This is a debug message.")
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
    logging.critical("This is a critical message.")

    # Test logging without file (console)
    # setup_logging(log_level_str="INFO")
    # logging.info("Info message to console.")
