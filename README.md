# DaTi*k*Z Dataset
[![DaTikZv1](https://img.shields.io/badge/DaTikZ--v1-blue?label=%F0%9F%A4%97%20Hugging%20Face&labelColor=gray)](https://huggingface.co/datasets/nllg/datikz)
[![DaTikZv2](https://img.shields.io/badge/DaTikZ--v2-blue?label=%F0%9F%A4%97%20Hugging%20Face&labelColor=gray)](https://huggingface.co/datasets/nllg/datikz-v2)

DaTi*k*Z is a dataset containing a wide variety of Ti*k*Z drawings. It is
intended to support research and development of machine learning models that
can generate or manipulate vector graphics in L<sup>A</sup>T<sub>E</sub>X.

There are two main distributions publicly available:
[DaTi*k*Z<sub>v1</sub>](https://huggingface.co/datasets/nllg/datikz)
(introduced in [AutomaTi*k*Z](https://github.com/potamides/AutomaTikZ)) and
[DaTi*k*Z<sub>v2</sub>](https://huggingface.co/datasets/nllg/datikz-v2)
(introduced in [DeTi*k*Zify](https://github.com/potamides/DeTikZify)). In
compliance with licensing agreements, certain Ti*k*Z drawings are excluded from
these public versions of the dataset. This repository provides tools and
methods to recreate the complete dataset from scratch.

> [!NOTE]
> The datasets you produce might vary slightly from the originally created
> ones, as the sources used for crawling are subject to continuous updates.

## Installation
DaTi*k*Z relies on a full [TeX Live](https://www.tug.org/texlive) installation
and also requires [ghostscript](https://www.ghostscript.com) and
[poppler](https://poppler.freedesktop.org). Python dependencies can be
installed as follows:
```sh
pip install -r requirements.txt
```
For processing [arXiv](https://arxiv.org) source files (optional), you
additionally need to preprocess arXiv bulk data using
[arxiv-latex-extract](https://github.com/potamides/arxiv-latex-extract).

## Usage
To generate the dataset, run the `main.py` script. Use the `--help` flag to
view the available options. The commands for the official distributions are as
follows:
* **DaTi*k*Z<sub>v1</sub>**: `main.py --arxiv_files "${DATIKZ_ARXIV_FILES[@]}" --size 334 --captionize`
* **DaTi*k*Z<sub>v2</sub>**: `main.py --arxiv_files "${DATIKZ_ARXIV_FILES[@]}" --size 386`

In this example, the `DATIKZ_ARXIV_FILES` environment variable should contain
the paths to either the `jsonl` files obtained with the arxiv-latex-extract
utility, or archives that include these files.

When executed successfully, the script generates the following output files:
* `datikz-raw.parquet`: The raw, unsplit dataset without additional
  augmentation.
* `datikz-train.parquet`: The training split of the DaTi*k*Z dataset.
* `datikz-test.parquet`: The test split consisting of 1k items.
