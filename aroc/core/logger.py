import sys
import io
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional

class ServerLogger:
    def __init__(self, max_log_entries: int = 10000):
        self.max_log_entries = max_log_entries
        self.log_history = deque(maxlen=max_log_entries)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.setup_logging()
        
    def setup_logging(self):
        # File logging setup
        file_handler = RotatingFileHandler(
            'server_logs.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Console logging setup
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Main logger setup
        self.logger = logging.getLogger('server_logger')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Redirect stdout and stderr
        sys.stdout = self.StreamLogger(self, 'stdout')
        sys.stderr = self.StreamLogger(self, 'stderr')
        
    class StreamLogger(io.TextIOBase):
        def __init__(self, parent, stream_type):
            self.parent = parent
            self.stream_type = stream_type
            self.buffer = []
            
        def write(self, text):
            if text.strip():  # Ignore empty lines
                timestamp = datetime.now().isoformat()
                log_entry = {
                    'timestamp': timestamp,
                    'type': self.stream_type,
                    'message': text.strip()
                }
                self.parent.log_history.append(log_entry)

                # Log the message as info
                self.parent.logger.info(text.strip())

                # Write to original stream
                if self.stream_type == 'stdout':
                    self.parent.original_stdout.write(text)
                else:
                    self.parent.original_stderr.write(text)
                    
        def flush(self):
            if self.stream_type == 'stdout':
                self.parent.original_stdout.flush()
            else:
                self.parent.original_stderr.flush()
                
    def log_event(self, level: str, message: str, data: Optional[Dict] = None):
        """Log an event with a specific level"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'data': data
        }
        
        self.log_history.append(log_entry)
        
        if level == 'debug':
            self.logger.debug(message, extra={'data': data})
        elif level == 'info':
            self.logger.info(message, extra={'data': data})
        elif level == 'warning':
            self.logger.warning(message, extra={'data': data})
        elif level == 'error':
            self.logger.error(message, extra={'data': data})
        elif level == 'critical':
            self.logger.critical(message, extra={'data': data})
            
    def get_log_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get log history with optional limit"""
        if limit is None:
            return list(self.log_history)
        return list(self.log_history)[-limit:]
        
    def clear_logs(self):
        """Clear log history"""
        self.log_history.clear()

server_logger: Optional[ServerLogger] = None


def init_server_logger(max_log_entries: int = 10000) -> ServerLogger:
    """Initialize global server logger if not already created."""
    global server_logger
    if server_logger is None:
        server_logger = ServerLogger(max_log_entries)
    return server_logger
