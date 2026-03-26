import logging
import json
import os
from datetime import datetime

def get_logger(name):
    """Get configured logger for Lambda functions"""
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_error(logger, error, context=None):
    """Log error with context"""
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.utcnow().isoformat(),
        'context': context or {}
    }
    logger.error(json.dumps(error_data))
