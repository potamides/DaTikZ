from contextlib import contextmanager
from datetime import datetime
from json import load
from urllib.request import urlopen

from datasets import (
    disable_progress_bar,
    enable_progress_bar,
    is_progress_bar_enabled,
)

def get_creation_time(repo):
    return datetime.strptime(load(urlopen(f"https://api.github.com/repos/{repo}"))['created_at'], "%Y-%m-%dT%H:%M:%SZ")

def lines_startwith(string, prefix):
    return all(line.startswith(prefix) for line in string.splitlines())

def lines_removeprefix(string, prefix):
    return "".join(line.removeprefix(prefix) for line in string.splitlines(keepends=True))

@contextmanager
def no_progress_bar():
    if is_progress_bar_enabled():
        try:
            yield disable_progress_bar()
        finally:
            enable_progress_bar()
