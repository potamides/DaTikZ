from glob import glob
from multiprocessing import Pool
from os.path import isdir, join

from datasets import load_dataset

from .. import no_progress_bar
from .finder import TikzFinder

def _load_worker(paper):
    found = list()
    try:
        for tikz in TikzFinder(tex=paper['text']).find(): # type: ignore
            found.append({
                "caption": tikz.caption,
                "code": tikz.code,
                "date": paper['meta']['timestamp'], # type: ignore
                "uri": paper['meta']['url'] # type: ignore
            })
    except (AssertionError, RecursionError): # FIXME: where does the recursion error come from?
        pass
    return found

def expand(files):
    for file in files:
        if isdir(file):
            yield from glob(join(file, "*.jsonl"))
        else:
            yield file

def load(files, bs=1):
    with no_progress_bar(), Pool(bs) as p:
        ds = load_dataset("json", data_files=list(expand(files)), split="train")
        for results in p.imap_unordered(_load_worker, ds):
            yield from results
