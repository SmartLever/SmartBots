""" Decorators
"""
import functools
import logging
logger = logging.getLogger(__name__)


def log_start_end(func=None, log=None):
    """Wrap function to add a log entry at execution start and end.

    Parameters
    ----------
    func : optional
        Function, by default None
    log : optional
        Logger, by default None

    Returns
    -------
        Wrapped function
    """
    assert callable(func) or func is None  # nosec

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            logging_name = ""
            logger_used = logging.getLogger(logging_name) if logging_name else log

            logger_used.info(
                "START",
                extra={"func_name_override": func.__name__},
            )
            try:
                value = func(*args, **kwargs)
                logger_used.info("END", extra={"func_name_override": func.__name__})
                return value
            except Exception as e:
                print(f"Error: {e}")
                logger_used.exception(
                    "Exception: %s",
                    str(e),
                    extra={"func_name_override": func.__name__},
                )
                return []

        return wrapper

    return decorator(func) if callable(func) else decorator



def check_api_key(api_keys):
    """
    Wrapper around the view or controller function and
    print message if API keys are not yet defined.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            from src.application import conf
            undefined_apis = []
            for key in api_keys:
                # Get value of the API Keys
                if getattr(conf, key) == "REPLACE_ME":
                    undefined_apis.append(key)

            if undefined_apis:
                undefined_apis_name = ", ".join(undefined_apis)
                print(f"{undefined_apis_name} not defined. ")
            else:
                return func(*args, **kwargs)
        return wrapper_decorator
    return decorator
