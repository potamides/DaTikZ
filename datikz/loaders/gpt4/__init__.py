from datetime import datetime
from importlib import import_module
from importlib.resources import files

from datasets import load_dataset

from .. import no_progress_bar


REPO = "potamides/DaTikZ"
TIKZ_DATA = str(files(import_module(__name__)) / "gpt4.json")

def load():
    with no_progress_bar():
        dataset = load_dataset("json", data_files=TIKZ_DATA, split="train")

    for idx, item in enumerate(dataset, 1):
        yield {
            "caption": item['caption'],
            "code": item['code'],
            "date": datetime.utcfromtimestamp(item['date']/1000),
            "uri": f"https://github.com/{REPO}/blob/main/datikz/loaders/gpt4/gpt4.json#L{idx}"
        }
