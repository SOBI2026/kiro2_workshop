import time
import json
from functools import wraps
from .logger import get_logger

logger = get_logger(__name__)

class RetryableError(Exception):
    """Error that should trigger retry logic"""
    pass

class ValidationError(Exception):
    """Error for invalid input data"""
    pass

def exponential_backoff_retry(max_retries=10, base_delay=0.1):
    """Decorator for exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {str(e)}")
                    time.sleep(delay)
        return wrapper
    return decorator

def handle_lambda_error(func):
    """Decorator for Lambda error handling"""
    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': str(e)})
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }
    return wrapper
