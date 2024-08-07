from glob import glob
from textwrap import dedent
from os.path import join, relpath, sep
from re import DOTALL, findall
from urllib.parse import quote

from TexSoup import TexSoup

from . import get_creation_time, lines_removeprefix, lines_startwith

REPO = "pgf-tikz/pgf"
CREATED = get_creation_time(REPO)

class CodeExample:
    def __init__(self, code, hidden=False, code_only=False, pre=None, post=None, preamble=None, render_instead=None):
        preamble = (preamble + "\n") if preamble else ""
        pre = (pre + "\n") if pre else ""
        code = render_instead if render_instead else code
        post = ("\n" + post) if post else ""
        self.code = self.format_as_document(preamble, pre + code + post)
        self.visible = not (hidden or code_only)

    def format_as_document(self, preamble, code):
        cls = "\\documentclass[tikz]{standalone}\n"
        doc = "{cls}{preamble}\n\\begin{{document}}\n\n{code}\n\n\\end{{document}}"
        return doc.format(cls=cls, preamble=preamble, code=code)

def extract_examples(doc):
    example_regex = r"(([^\n]*?)\\begin{codeexample}.*?\\end{codeexample})"
    for example, prefix in findall(example_regex, doc, DOTALL):
        if len(prefix) > 0 and not prefix.strip():
            example = dedent(example)
        elif lines_startwith(dedented:=dedent(example), "%"):
            example = dedent(lines_removeprefix(dedented, "%"))
        else:
            example = example.removeprefix(prefix)
        soup = TexSoup(example, tolerance=1)
        code = soup.codeexample.expr.string.strip() # type: ignore
        args = dict()
        soupiter = iter(soup.codeexample.args[0].all) # type: ignore
        while item:=next(soupiter, None):
            assert isinstance(item, str)
            for t in item.split(","):
                match t.strip():
                    case ("hidden" | "code only") as arg:
                        args[arg.replace(" ", "_")] = True
                    case ('pre=' | 'post=' | 'preamble=' | 'render instead=') as arg:
                        args[arg.replace(" ", "_")[:-1]] = next(soupiter).string.strip()
                    case arg if arg.endswith("="):
                        next(soupiter) # consume argument we don't use
        yield CodeExample(code=code, **args)

def load(directory):
    for file in glob(join(directory, "pgf-*/doc/generic/pgf/*.tex")):
        with open(file, 'r') as f:
            for example in extract_examples(f.read().strip()):
                if example.visible:
                    yield {
                        "caption": "",
                        "code": example.code,
                        "date": CREATED,
                        "uri": join(f"https://github.com/{REPO}/blob/master", quote(relpath(file, directory).split(sep, 1)[1]))
                    }

if __name__ == "__main__":
    for example in load("/home/amnifilius/Downloads"):
        input(example['code'])
