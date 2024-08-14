from re import sub

from svg2tikz import convert_svg

from . import get_creation_time, no_progress_bar
from datasets import load_dataset

REPO = "evanthebouncy/chatgpt-svg"
CREATED = get_creation_time(REPO)

def convert(svg):
    tikz = convert_svg(svg, wrap=True, crop=True, round_number=2)
    tikz = sub(4 * '\n', "\n", tikz).strip()
    return tikz

def load(tsv):
    with no_progress_bar():
        dataset = load_dataset("csv", sep="\t", data_files=tsv, split="train")
        for idx, item in enumerate(dataset, 1):
            caption = item['prompt'].removeprefix("Using the SVG format, output ").split(".")[0] + "."
            tikz = convert(item['svg'])

            yield {
                "caption": caption,
                "code": tikz,
                "date": CREATED,
                "uri": f"https://github.com/{REPO}/blob/master/data.tsv#L{idx}"
            }
