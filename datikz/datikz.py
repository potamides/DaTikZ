"""
Combination of various sources of tikz descriptions with aligned code.
"""

from functools import partial
from glob import glob
from io import BytesIO
from itertools import islice
from multiprocessing.pool import Pool
from operator import or_
from os import getpgid, killpg
from os.path import isdir, join
from re import sub
from signal import SIGKILL
from subprocess import CalledProcessError, DEVNULL, Popen, TimeoutExpired
from tempfile import NamedTemporaryFile, TemporaryDirectory

from PIL import ImageOps
from datasets import Features, Image, Value, builder
from datasets.info import DatasetInfo
from datasets.splits import Split, SplitGenerator
from datasets.utils import logging
from pdf2image.exceptions import PDFPageCountError
from pdf2image.pdf2image import convert_from_path
from pdfCropMargins import crop
import pymupdf
from pymupdf import EmptyFileError
from regex import search

from datikz.loaders import (
    arxiv,
    chatgpt,
    gpt4,
    janosh_tikz,
    latex_examples,
    petarv_tikz,
    pgfmanual,
    tex_stackexchange_com,
    texample_net,
    tikz_favorites,
    tikz_net,
    openaiwatch,
)

logger = logging.get_logger("datasets")

def batched(iterable, n):
    it = iter(iterable)
    while (batch := tuple(islice(it, n))):
        yield batch

# https://alexandra-zaharia.github.io/posts/kill-subprocess-and-its-children-on-timeout-python
def run(*popenargs, timeout=None, **kwargs):
    with Popen(*popenargs, start_new_session=True, **kwargs) as p:
        try:
            stdout, stderr = p.communicate(timeout=timeout)
        except TimeoutExpired:
            killpg(getpgid(p.pid), SIGKILL)
            p.wait()
            raise
        except:
            killpg(getpgid(p.pid), SIGKILL)
            raise
        if retcode := p.poll():
            raise CalledProcessError(retcode, p.args, output=stdout, stderr=stderr)

def tex2img(code, size=384, timeout=120, expand_to_square=True):
    codelines = code.split("\n")
    # make sure we don't have page numbers in compiled pdf (for cropping)
    codelines.insert(1, r"{cmd}\AtBeginDocument{{{cmd}}}".format(cmd=r"\thispagestyle{empty}\pagestyle{empty}"))

    def try_compile(file):
        open(f"{file}.bbl", 'a').close() # some classes expect a bibfile
        for engine in ["pdflatex", "lualatex", "xelatex"]: # could also try: https://tex.stackexchange.com/a/495999
            try:
                run(
                    args=["latexmk", "-nobibtex", "-norc", "-interaction=nonstopmode", f"-{engine}", file],
                    cwd=tmpdirname,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    timeout=timeout
                )
                return f"{file}.pdf"
            except CalledProcessError:
                continue
        raise ValueError("Couldn't compile latex source.")

    with TemporaryDirectory(ignore_cleanup_errors=True) as tmpdirname:
        with NamedTemporaryFile(dir=tmpdirname, buffering=0) as tmpfile:
            # compile
            tmpfile.write("\n".join(codelines).encode())
            pdfname = try_compile(tmpfile.name)

            # extract last page
            doc = pymupdf.open(pdfname)
            doc.select([len(doc)-1])
            doc.saveIncr()

            # crop
            crop(["-c", "gb", "-p", "0", "-a", "-1", "-o", cropname := f"{tmpfile.name}-cropped.pdf", pdfname], quiet=True)
            #run(["pdfcrop", cropname := f"{tmpfile.name}.pdf", cropname], check=True, cwd=tmpdirname)

            # rasterize
            image = convert_from_path(cropname, size=size, single_file=True)[0]
            if expand_to_square:
                image = ImageOps.pad(image, (size, size), color='white')

            # test if we have content
            if image.getcolors(1) is not None:
                raise ValueError("Provided code compiled to an empty image.")

            # return pdf and rasterized image
            with open(cropname, "rb") as f:
                pdf = f.read()
                image.save(imgByteArr:=BytesIO(), format="PNG")
                raster = imgByteArr.getvalue()
                return {"pdf": pdf, "image": raster}

def texse_gen(xml_path): return tex_stackexchange_com.TeXExchangeParser(xml_path).load()


class TikZConfig(builder.BuilderConfig):
    """BuilderConfig for TikZ."""

    def __init__(self, *args, bs=8, size=384, arxiv_files=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.bs = bs
        self.size = size
        self.data_urls = {
            "PetarV-/TikZ": "https://github.com/PetarV-/TikZ/archive/refs/heads/master.zip",
            "janosh/tikz": "https://github.com/janosh/tikz/archive/refs/heads/main.zip",
            "tikz_favorites": "https://github.com/f0nzie/tikz_favorites/archive/refs/heads/master.zip",
            "LaTeX-examples": "https://github.com/MartinThoma/LaTeX-examples/archive/refs/heads/master.zip",
            "pgfmanual": "https://github.com/pgf-tikz/pgf/archive/refs/heads/master.zip",
            "chatgpt": "https://github.com/evanthebouncy/chatgpt-svg/raw/master/data.tsv",
            "openaiwatch": "https://hf.co/datasets/yuntian-deng/openaiwatch/resolve/main/data/train-00000-of-00001.parquet",
            "arxiv": list(arxiv.expand(arxiv_files)),
            "tex.stackexchange.com": "https://archive.org/download/stackexchange/tex.stackexchange.com.7z/Posts.xml",
        }
        self.generators = {
            "PetarV-/TikZ": petarv_tikz.load,
            "janosh/tikz": janosh_tikz.load,
            "tikz_favorites": tikz_favorites.load,
            "LaTeX-examples": latex_examples.load,
            "pgfmanual": pgfmanual.load,
            "chatgpt": chatgpt.load,
            "openaiwatch": openaiwatch.load,
            "gpt4": gpt4.load,
            "texample.net": texample_net.load,
            "tikz.net": tikz_net.load,
            "pgfplots.net": tikz_net.load, # tikz.net downloader also works for this site
            "arxiv": arxiv.load,
            "tex.stackexchange.com": texse_gen
        }


class TikZ(builder.GeneratorBasedBuilder):
    """A TikZ corpus."""

    BUILDER_CONFIG_CLASS = TikZConfig

    def _info(self):
        features = {
            "caption": Value("string"),
            "code": Value("string"),
            "image": Image(),
            "pdf": Value("binary"),
            "uri": Value("string"),
            "origin": Value("string"),
            "date": Value("timestamp[us]"),
        }

        return DatasetInfo(
            description=str(__doc__),
            features=Features(features),
        )
    def _split_generators(self, dl_manager):
        urls_to_download = self.config.data_urls # type: ignore
        extracted_files = dl_manager.download_and_extract(urls_to_download)

        return [
            SplitGenerator(
                name=str(Split.TRAIN), gen_kwargs={"datasets": extracted_files}
            ),
        ]

    def _filter_comments(self, text, patterns=r"\{}$&#&_" + "[]"):
        """
        Removes all comments that match the patterns. By default patterns are
        characters with catcodes 1-8 and a few other symbols often used inside
        TikZ code.

        This may be useful for arXiv, because tikzpictures retrieved from there
        sometimes contain old code, commented out. This is an attempt to remove
        such comments.
        """
        if text.lstrip().startswith("%") and any(pattern in text for pattern in patterns):
            return ""
        match = search(r"(?<![^\\]\\(\\{2})*)%", text)
        if match:
            end = match.end()
            if any(pattern in text[end:] for pattern in patterns):
                endpos = end - 1 if not text[end - 2].strip() else end
                return text[:endpos].rstrip() + "\n"
        return text

    def _clean(self, example, full=False):
        for key, maybe_text in example.items():
            try:
                example[key] = sub(r"\r\n|\r", r"\n", maybe_text).strip() # normalize newlines
            except TypeError:
                pass
        # first remove leading comments only...
        example["code"] = sub(r"^(%.*\n)*", "", example["code"]).strip()
        if full: # ...and maybe also remove all other comments
            example["code"] = "".join(
                self._filter_comments(line)
                for line in example["code"].splitlines(keepends=True)
            ).strip()

        return example

    def _compile(self, ex):
        output = tex2img(ex["code"], size=self.config.size) # type: ignore
        ex["image"] = {"path": None, "bytes": output['image']}
        ex["pdf"] = output['pdf']
        return ex

    def _generate_examples(self, datasets):
        all_tikz, generators = set(), self.config.generators # type: ignore
        skipped, idx = 0, 1

        def preprocess(load, full_clean=False, *args, **kwargs):
            for ex in load(*args, **kwargs):
                ex = self._clean(ex, full=full_clean)
                if ex['code'] not in all_tikz:
                    all_tikz.add(ex['code'])
                    yield ex

        def skip_on_error(loader):
            nonlocal skipped
            while True:
                try:
                    yield next(loader)
                except (ValueError, PDFPageCountError, TimeoutExpired, CalledProcessError, EmptyFileError):
                    skipped += 1
                except StopIteration:
                    break

        for name, load in zip(generators.keys(), (partial(preprocess, load) for load in generators.values())):
            logger.debug("Processing examples from '%s'.", name)
            match name:
                case "arxiv": loader = load(files=datasets[name], full_clean=True, bs=self.config.bs) # type: ignore
                case "chatgpt": loader = load(tsv=datasets[name])
                case "openaiwatch": loader = map(partial(or_, dict(origin="gpt4")), load(parquet=datasets[name]))
                case "tex.stackexchange.com": loader = load(xml_path=datasets[name])
                case "texample.net" | "tikz.net" | "gpt4": loader = load()
                case "pgfplots.net": loader = load(base_url=f"https://{name}")
                case _: loader = load(directory=datasets[name])

            with Pool(self.config.bs) as p: # type: ignore
                for example in skip_on_error(p.imap_unordered(self._compile, loader)):
                    example["origin"] = example.get("origin", name)
                    yield idx, example
                    idx += 1

        if skipped:
            logger.warning(f"Couldn't compile {skipped}/{skipped+idx-1} documents.")
