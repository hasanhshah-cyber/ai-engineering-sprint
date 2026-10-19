# Day 6: A HuggingFace Model Running on My Own Machine

A small HuggingFace model (`Xenova/flan-t5-small`, the ONNX version of
`google/flan-t5-small`, about 80M parameters) downloaded once, then running
locally with ONNX Runtime. No API key. No cloud call.

## Why ONNX Runtime, used directly

PyTorch no longer ships wheels for Intel Macs, so `pip install torch`
fails on this machine with "no matching distribution found." The usual
ONNX helper, optimum, itself depends on torch, so it cannot install
either. This script talks to ONNX Runtime directly with plain numpy
arrays. No torch, no optimum. Same model, same demos, no heavy engine.

## What it does

`local_model.py` runs the same small model two ways:

1. Summarizes a short paragraph about the sprint.
2. Answers a question from a short context.

## Run it

First run downloads the model files (about 565 MB) from HuggingFace.
After that it runs offline.

```bash
cd day-6-local-model
python3 -m venv .venv
source .venv/bin/activate
pip install --only-binary :all: -r requirements.txt
python3 local_model.py
```

The `--only-binary :all:` flag tells pip to use ready-made wheels only.
Without it, pip can fall back to building a package from source, and that
build is broken for some packages.

If you already made the `.venv` folder, skip the `python3 -m venv` line and
just activate it, then install and run.

## Honest notes

- This is a small model. Its answers are short and sometimes plain. That is
  the tradeoff for running on a laptop with no API key.
- First run needs internet to download the model. Later runs do not.
- ONNX Runtime is much lighter to install than torch, which is why this
  version works on Intel Macs.
