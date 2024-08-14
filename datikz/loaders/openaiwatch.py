from bs4 import BeautifulSoup
from datasets import load_dataset
from markdown import markdown

from . import no_progress_bar

def load(parquet, sample_size=300):
    with no_progress_bar():
        dataset = load_dataset("parquet", data_files=parquet, split="train")
        dataset = dataset.add_column("idx", range(len(dataset))) # type: ignore
        dataset = dataset.filter(lambda ex: ex['model'].startswith("gpt-4"))

    duplicates = set()
    for ex in dataset.shuffle():
        soup = BeautifulSoup(markdown(ex['raw_response'], extensions=['fenced_code']), 'html.parser')
        code = getattr(soup.code, "string", "").strip()

        if code not in duplicates and code.startswith(r"\documentclass") and "tikzpicture" in code:
            duplicates.add(code)
            yield {
                "caption": "Draw a unicorn in TikZ:",
                "code": code,
                "date": ex['timestamp'],
                "uri": f"https://huggingface.co/datasets/yuntian-deng/openaiwatch?row={ex['idx']}"
            }
            if (sample_size:=sample_size-1) <= 0:
                break
