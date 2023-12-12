from glob import glob
from os.path import basename, join, relpath, sep
from urllib.parse import quote

from . import get_creation_time

REPO = "f0nzie/tikz_favorites"
CREATED = get_creation_time(REPO)

def load(directory):
    for file in glob(join(directory, "tikz_favorites-*/src/*.tex")):
        with open(file, 'r') as f:
            code = f.read().strip()
            descr, _, tags = basename(file).split(".")[0].replace("_", " ").partition("+")

        yield {
            "caption": (f"{descr} ({tags.replace('+', ', ')})") if tags else descr,
            "code": code,
            "date": CREATED,
            "uri": join(f"https://github.com/{REPO}/blob/master", quote(relpath(file, directory).split(sep, 1)[1]))
        }
