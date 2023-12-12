from glob import glob
from os.path import basename, dirname, join, relpath, sep
from urllib.parse import quote

from . import get_creation_time

REPO = "MartinThoma/LaTeX-examples"
CREATED = get_creation_time(REPO)

def load(directory):
    for file in glob(join(directory, "LaTeX-examples-*/tikz/*/*.tex")):
        with open(file, 'r') as f:
            code = f.read().strip()
            descr = basename(file).removesuffix(".tex").replace("-", " ")

        yield {
            "caption": descr,
            "code": code,
            "date": CREATED,
            "uri": join(f"https://github.com/{REPO}/blob/master", quote(relpath(dirname(file), directory).split(sep, 1)[1]))
        }
