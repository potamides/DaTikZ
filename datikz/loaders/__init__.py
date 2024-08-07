from datetime import datetime
from json import load
from urllib.request import urlopen

from datasets import (
    disable_progress_bar,
    enable_progress_bar,
    is_progress_bar_enabled,
    load_dataset,
)

def get_creation_time(repo):
    return datetime.strptime(load(urlopen(f"https://api.github.com/repos/{repo}"))['created_at'], "%Y-%m-%dT%H:%M:%SZ")

def lines_startwith(string, prefix):
    return all(line.startswith(prefix) for line in string.splitlines())

def lines_removeprefix(string, prefix):
    return "".join(line.removeprefix(prefix) for line in string.splitlines(keepends=True))

def load_silent(*args, **kwargs):
    if is_progress_bar_enabled():
        disable_progress_bar()
        dataset = load_dataset(*args, **kwargs)
        enable_progress_bar()
    else:
        dataset = load_dataset(*args, **kwargs)

    return dataset
