import json
import os
import socket
from datetime import datetime
import logging
import logging.config

class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        # Get these once during initialization for efficiency
        self.hostname = socket.gethostname()
        # Get the script name from the main module
        import __main__
        self.script_name = os.path.basename(getattr(__main__, '__file__', 'interactive'))

    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname.lower(),
            'message': record.getMessage(),
            'source': self.script_name,
            'host': self.hostname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_entry)

def setup_logging(config_path='logging_config.json', log_file_path=None, fluentd_host=None, fluentd_port=24224):
    """
    Setup logging configuration from JSON file with optional Fluentd support

    Args:
        config_path: Path to the JSON config file
        log_file_path: Override the log file path (optional)
        fluentd_host: Fluentd server IP/hostname (optional)
        fluentd_port: Fluentd server port (default: 24224)
    """
    # Load the JSON config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Update log file path if provided
    if log_file_path:
        config['handlers']['file']['filename'] = log_file_path

    # Add Fluentd handler if host is provided
    if fluentd_host:
        try:
            # Import fluent handler
            from fluent import handler

            # Add fluent handler to config
            config['handlers']['fluent'] = {
                'class': 'fluent.handler.FluentHandler',
                'host': fluentd_host,
                'port': fluentd_port,
                'tag': 'python.logs',
                'level': 'INFO'
            }

            # Add fluent handler to root logger
            config['root']['handlers'].append('fluent')

        except ImportError:
            print("Warning: fluent-logger not installed. Install with: pip install fluent-logger")

    # Apply the configuration
    logging.config.dictConfig(config)

    return logging.getLogger(__name__)
