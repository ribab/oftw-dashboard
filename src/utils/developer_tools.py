import socket
import functools
import time
import logging

def find_available_port():
    """
    Find an available port on localhost for development.
    
    Returns:
        int or None: An available port number between 8000 and 40000, or None if no ports are available.
        
    Notes:
        - Searches in range 8000-40000 to avoid well-known ports (<1024) and ephemeral ports (>49151)
        - Starts with common web application ports in the 8000s
    """
    for port in range(8000, 40000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # connect_ex returns 0 if connection succeeds (port is in use)
            # and non-zero if connection fails (port is available)
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

def log_function_call(func):
    """
    A decorator that logs the entry and exit of a function.
    
    Args:
        func: The function to be wrapped.
        
    Returns:
        The wrapped function with logging capabilities.
        
    Example:
        @function_logger
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        logging.debug(f"Entering function: {function_name}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logging.debug(f"Exiting function: {function_name} (execution time: {elapsed_time:.4f}s)")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logging.error(f"Exception in {function_name} after {elapsed_time:.4f}s: {str(e)}")
            raise
    
    return wrapper

def enable_debug_logging():
    logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    @log_function_call
    def my_function(arg1, arg2):
        print('We are in example function')

    enable_debug_logging()
    
    my_function(1, 2)
