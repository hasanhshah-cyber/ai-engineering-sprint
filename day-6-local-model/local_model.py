"""Day 6: a HuggingFace model running on this machine.

No API key. No cloud call. The model downloads once from HuggingFace,
then runs locally.

Model: Xenova/flan-t5-small, the ONNX version of google/flan-t5-small
(about 80M parameters, small enough for a laptop).

Why ONNX Runtime, used directly: PyTorch no longer ships wheels for Intel
Macs, so torch cannot install on this machine. And optimum, the usual
helper for ONNX models, itself depends on torch. So this script talks to
ONNX Runtime directly with plain numpy arrays. No torch, no optimum.
Same model, same demos, no heavy engine.
"""

import os

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

MODEL_NAME = "Xenova/flan-t5-small"

# Only these files are downloaded, not the whole repo with its quantized
# variants.
ALLOW_PATTERNS = [
    "config.json",
    "generation_config.json",
    "onnx/encoder_model.onnx",
    "onnx/decoder_model.onnx",
    "onnx/decoder_with_past_model.onnx",
    "special_tokens_map.json",
    "spiece.model",
    "tokenizer.json",
    "tokenizer_config.json",
]


def run(tokenizer, encoder, decoder, prompt, max_length=60):
    """Run one prompt through the local model with greedy decoding."""
    inputs = tokenizer(prompt, return_tensors="np")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # Encode once. The decoder reuses this on every step.
    encoder_hidden = encoder.run(
        None,
        {"input_ids": input_ids, "attention_mask": attention_mask},
    )[0]

    # T5 starts decoding from the pad token (0) and stops at EOS (1).
    start_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    eos_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 1
    decoder_ids = np.array([[start_id]], dtype=np.int64)

    for _ in range(max_length):
        logits = decoder.run(
            None,
            {
                "input_ids": decoder_ids,
                "encoder_attention_mask": attention_mask,
                "encoder_hidden_states": encoder_hidden,
            },
        )[0]
        next_id = int(np.argmax(logits[0, -1]))
        if next_id == eos_id:
            break
        decoder_ids = np.concatenate(
            [decoder_ids, np.array([[next_id]], dtype=np.int64)], axis=1
        )

    return tokenizer.decode(decoder_ids[0], skip_special_tokens=True)


def main():
    print("Loading model:", MODEL_NAME)
    print("Running locally with ONNX Runtime. No API key used.")
    print()

    if os.path.isdir(MODEL_NAME):
        model_dir = MODEL_NAME
    else:
        model_dir = snapshot_download(MODEL_NAME, allow_patterns=ALLOW_PATTERNS)

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    encoder = ort.InferenceSession(
        os.path.join(model_dir, "onnx", "encoder_model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    decoder = ort.InferenceSession(
        os.path.join(model_dir, "onnx", "decoder_model.onnx"),
        providers=["CPUExecutionProvider"],
    )

    # Demo 1: summarize a short paragraph.
    paragraph = (
        "Hasan is building an AI engineering sprint. Each day he builds one "
        "small project that talks to a real tool or a real API. Day one was a "
        "chatbot that answers from his own documents. Day five was an agent "
        "that calls the GitHub API and lists his public repositories."
    )
    summary = run(tokenizer, encoder, decoder, "summarize: " + paragraph)
    print("SUMMARY")
    print("Input: " + paragraph)
    print("Local model output: " + summary)
    print()

    # Demo 2: answer a question from a short context.
    context = (
        "The agent calls the GitHub API and lists the user's public "
        "repositories. It needs no GitHub token because it only reads "
        "public data."
    )
    question = "What does the agent do?"
    answer = run(
        tokenizer,
        encoder,
        decoder,
        "question: " + question + " context: " + context,
    )
    print("QUESTION ANSWERING")
    print("Question: " + question)
    print("Local model output: " + answer)


if __name__ == "__main__":
    main()
