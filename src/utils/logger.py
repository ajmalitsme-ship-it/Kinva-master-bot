"""
Logger - Logging configuration and utilities
Author: @kinva_master
"""

import os
import sys
import logging
import json
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional
import inspect

from ..config import Config

# Log levels
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

# Logger instances
_loggers = {}


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_tb(record.exc_info[2]))
            }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class ContextLogger:
    """Logger with context support"""
    
    def __init__(self, name: str, context: Dict = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        extra = kwargs.pop('extra', {})
        extra.update(self.context)
        
        # Add user context if available
        if hasattr(inspect.currentframe().f_back, 'f_locals'):
            locals_dict = inspect.currentframe().f_back.f_locals
            if 'user_id' in locals_dict:
                extra['user_id'] = locals_dict['user_id']
            if 'request_id' in locals_dict:
                extra['request_id'] = locals_dict['request_id']
        
        self.logger.log(level, msg, *args, extra=extra, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, exc_info=True, **kwargs)
    
    def with_context(self, **kwargs) -> 'ContextLogger':
        """Create new logger with additional context"""
        new_context = self.context.copy()
        new_context.update(kwargs)
        return ContextLogger(self.logger.name, new_context)


def setup_logger(name: str = 'kinva_master', 
                 level: str = None,
                 log_file: str = None,
                 console: bool = True,
                 json_format: bool = False) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        level: Log level (debug, info, warning, error, critical)
        log_file: Log file path
        console: Enable console output
        json_format: Use JSON format for logs
    
    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Set level
    level_name = (level or Config.LOG_LEVEL).lower()
    logger.setLevel(LOG_LEVELS.get(level_name, logging.INFO))
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        if not json_format:
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        else:
            console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Use rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None, context: Dict = None) -> ContextLogger:
    """
    Get logger instance with optional context
    
    Args:
        name: Logger name (default: 'kinva_master')
        context: Initial context data
    
    Returns:
        ContextLogger instance
    """
    if name is None:
        name = 'kinva_master'
    
    # Create logger if not exists
    if name not in _loggers:
        _loggers[name] = setup_logger(name)
    
    logger = _loggers[name]
    return ContextLogger(logger.name, context or {})


def log_error(error: Exception, context: Dict = None, 
              user_id: int = None, **kwargs):
    """
    Log error with context
    
    Args:
        error: Exception object
        context: Additional context
        user_id: User ID if available
        **kwargs: Additional fields
    """
    logger = get_logger('error')
    
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        **kwargs
    }
    
    if user_id:
        error_data['user_id'] = user_id
    
    if context:
        error_data['context'] = context
    
    logger.error(f"Error occurred: {error}", extra=error_data)


def log_user_activity(user_id: int, action: str, details: Dict = None, **kwargs):
    """
    Log user activity
    
    Args:
        user_id: User ID
        action: Action performed
        details: Additional details
        **kwargs: Additional fields
    """
    logger = get_logger('activity')
    
    activity_data = {
        'user_id': user_id,
        'action': action,
        'details': details or {},
        **kwargs
    }
    
    logger.info(f"User activity: {action}", extra=activity_data)


def log_api_call(endpoint: str, method: str, user_id: int = None,
                status_code: int = None, duration: float = None,
                **kwargs):
    """
    Log API call
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        user_id: User ID
        status_code: Response status code
        duration: Request duration in seconds
        **kwargs: Additional fields
    """
    logger = get_logger('api')
    
    api_data = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'duration': duration,
        **kwargs
    }
    
    if user_id:
        api_data['user_id'] = user_id
    
    logger.info(f"API call: {method} {endpoint} - {status_code}", extra=api_data)


def log_payment(user_id: int, amount: float, currency: str, 
                method: str, status: str, payment_id: str = None,
                **kwargs):
    """
    Log payment transaction
    
    Args:
        user_id: User ID
        amount: Payment amount
        currency: Currency code
        method: Payment method
        status: Payment status
        payment_id: Payment ID
        **kwargs: Additional fields
    """
    logger = get_logger('payment')
    
    payment_data = {
        'user_id': user_id,
        'amount': amount,
        'currency': currency,
        'method': method,
        'status': status,
        'payment_id': payment_id,
        **kwargs
    }
    
    logger.info(f"Payment: {method} - {amount} {currency} - {status}", 
                extra=payment_data)


def log_security_event(event_type: str, user_id: int = None,
                      ip_address: str = None, details: Dict = None,
                      **kwargs):
    """
    Log security event
    
    Args:
        event_type: Security event type
        user_id: User ID
        ip_address: IP address
        details: Event details
        **kwargs: Additional fields
    """
    logger = get_logger('security')
    
    security_data = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'details': details or {},
        **kwargs
    }
    
    logger.warning(f"Security event: {event_type}", extra=security_data)


def log_performance(operation: str, duration: float, user_id: int = None,
                   **kwargs):
    """
    Log performance metrics
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        user_id: User ID
        **kwargs: Additional fields
    """
    logger = get_logger('performance')
    
    perf_data = {
        'operation': operation,
        'duration': duration,
        **kwargs
    }
    
    if user_id:
        perf_data['user_id'] = user_id
    
    logger.debug(f"Performance: {operation} took {duration:.4f}s", extra=perf_data)


class RequestLogger:
    """Request logging middleware"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger('request')
    
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        
        start_time = datetime.now()
        
        # Log request
        self.logger.info(
            f"Request: {scope['method']} {scope['path']}",
            extra={
                'method': scope['method'],
                'path': scope['path'],
                'client': scope.get('client'),
                'headers': dict(scope.get('headers', []))
            }
        )
        
        # Process request
        try:
            response = await self.app(scope, receive, send)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log response
            self.logger.info(
                f"Response: {scope['method']} {scope['path']} - {duration:.4f}s",
                extra={
                    'method': scope['method'],
                    'path': scope['path'],
                    'duration': duration,
                    'status': getattr(response, 'status_code', None)
                }
            )
            
            return response
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            log_error(e, context={
                'method': scope['method'],
                'path': scope['path'],
                'duration': duration
            })
            raise


# Create default logger instance
logger = get_logger()
