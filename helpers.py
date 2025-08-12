# helpers.py
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=1)


def run_in_thread(fn, *args, **kwargs):
    """Run a blocking function in a background thread and return a Future."""
    return _executor.submit(fn, *args, **kwargs)
