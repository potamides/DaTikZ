#!/usr/bin/env python
from argparse import ArgumentParser
from datetime import datetime
from os.path import abspath
from multiprocessing import set_start_method
import random
import sys

from datasets import disable_caching, load_dataset
import numpy.random
import pymupdf
from sacremoses import MosesTokenizer

MIN_CAPTION_LENGTH = 30
CUTOFF_DATE = datetime(2024, 1, 1)
MODELS = {"chatgpt", "gpt4"}
TEST_EXCLUDE = {
    "https://arxiv.org/abs/2303.12712",  # contains GPT-4 generated tikzpictures
    "https://arxiv.org/abs/2310.00367"  # contains AutomaTikZ generated tikzpictures
    "https://arxiv.org/abs/2405.15306"  # contains DeTikZify generated tikzpictures
}

tokenize = MosesTokenizer().tokenize

def set_seed(seed):
    random.seed(seed)
    numpy.random.seed(seed)

def is_test_candidate(ex):
    """
    Returns True for human-generated examples newer than llama and not from
    github/stackexchange which are "good" (i.e., >=30 caption tokens heuristic).
    """
    return (
        not ex["origin"] in MODELS | {"tex.stackexchange.com"}
        and not "github" in ex["uri"]
        and not ex["uri"] in TEST_EXCLUDE
        and not "example-image" in ex["code"]
        and ex["date"] >= CUTOFF_DATE
        and len(tokenize(ex["caption"])) >= MIN_CAPTION_LENGTH
    )

def random_substring(string, length=50):
   start = random.randint(0, max(0, len(string) - length))
   return string[start:start+length]

def is_contaminated(ex, code, steps=3):
    """OpenAI decontamination method"""
    substrs = {random_substring(ex['code']) for _ in range(steps)}
    return any(any(s in c for s in substrs) for c in code if c != ex['code'])

def train_test_split(dataset, test_size=1000):
    cand = dataset.filter(lambda ex, code=dataset['code']: is_test_candidate(ex) and not is_contaminated(ex, code))
    cand = cand.add_column("labels", cand.class_encode_column("origin")['origin']).class_encode_column("labels")

    _, test = cand.train_test_split(test_size=test_size, stratify_by_column="labels").values()
    train = dataset.filter(lambda ex, code=set(test['code']): ex['code'] not in code)

    return train, test.remove_columns("labels")

def concat(caption, description):
    caption, description = caption.strip(), description.replace("\n", " ").strip()
    if caption:
        caption = caption[0].upper() + caption[1:]
        caption = caption if caption[-1] in ".!?"  else caption + "."
        return " ".join([caption, description]).strip()
    return description

def parse_args():
    argument_parser = ArgumentParser(
        description="Generate the DaTikZ dataset from scratch"
    )
    argument_parser.add_argument(
        "--arxiv_files",
        nargs='*',
        default=[],
        type=abspath,
        help="list of directories with files created by arxiv-latex-extract or archives containing them"
    )
    argument_parser.add_argument(
        "--size",
        default=384,
        type=int,
        help="resolution when rasterizing PDFs to PNGs"
    )
    argument_parser.add_argument(
        "--num_arxiv_workers",
        default=8,
        type=int,
        help="number of workers for extracting TikZ pictures extracting from arXiv"
    )
    argument_parser.add_argument(
        "--num_compile_workers",
        default=8,
        type=int,
        help="number of workers for compiling LaTeX"
    )

    return argument_parser.parse_args()

if __name__ == "__main__":
    set_seed(0)
    disable_caching()
    set_start_method("forkserver")
    pymupdf.TOOLS.mupdf_display_errors(False)
    args = parse_args()
    sys.argv = sys.argv[:1] # FIXME: ugly workaround to prevent svg2tikz from consuming script args
    datikz = load_dataset("datikz", split="train", trust_remote_code=True, **vars(args))
    train, test = train_test_split(datikz)

    train.to_parquet("datikz-train.parquet", compression="GZIP") # type: ignore
    test.to_parquet("datikz-test.parquet", compression="GZIP") # type: ignore
