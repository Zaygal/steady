#!/usr/bin/env python3
"""LoRA SFT on Tinker, then a fair baseline-vs-fine-tuned evaluation.

The metric is deliberately blunt and checkable: does the reply reuse a content word from the
person's own note? That is the one behaviour the baseline model gets wrong.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "agent"))
import steady  # noqa: E402

BASE = os.environ.get("TINKER_BASE_MODEL", "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16")
EPOCHS = int(os.environ.get("TINKER_EPOCHS", "3"))
LR = float(os.environ.get("TINKER_LR", "1e-4"))

STOP = set("""a an the and or but if i im i'm my me you your it its to of in on at for with is
it's just that this be been was were do does did have has had can could would should not no yes
about and then than so very really now here there""".split())


def content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']{3,}", text.lower()) if w not in STOP}


def uses_detail(note: str, reply: str) -> bool:
    return bool(content_words(note) & content_words(reply))


def load(name: str) -> list[dict]:
    return [json.loads(l) for l in (HERE / name).read_text().splitlines() if l.strip()]


def render(tok, note: str):
    messages = [{"role": "system", "content": steady.SYSTEM_POLICY + "\n\n" + steady.MODES["craving"]},
                {"role": "user", "content": note}]
    try:
        return tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    except Exception:                      # no chat template installed
        flat = "SYSTEM: " + messages[0]["content"] + "\nUSER: " + note + "\nASSISTANT:"
        return tok.encode(flat)


def evaluate(sampler, tok, held: list[dict], label: str, n: int = 60) -> dict:
    hits, lens = 0, []
    samples = []
    for row in held[:n]:
        ids = render(tok, row["note"])
        out = sampler.sample(
            prompt_type=None,
            prompt=None) if False else sampler.sample(
            prompt=__import__("tinker").types.ModelInput.from_ints(tokens=ids),
            sampling_params=__import__("tinker").types.SamplingParams(max_tokens=140, temperature=0.6),
            num_samples=1).result()
        reply = tok.decode(out.sequences[0].tokens).strip()
        hits += uses_detail(row["note"], reply)
        lens.append(len(reply.split()))
        if len(samples) < 5:
            samples.append({"note": row["note"], "reply": reply,
                            "used_detail": uses_detail(row["note"], reply)})
    return {"label": label, "n": len(held[:n]),
            "used_detail_pct": round(100 * hits / max(1, len(held[:n])), 1),
            "mean_words": round(sum(lens) / max(1, len(lens)), 1),
            "samples": samples}


def main() -> int:
    import numpy as np
    import tinker
    from tinker import types

    if not os.environ.get("TINKER_API_KEY"):
        print("no TINKER_API_KEY - refusing to pretend a fine-tune happened", file=sys.stderr)
        return 2

    train = load("train.jsonl")
    held = load("heldout.jsonl")
    svc = tinker.ServiceClient()
    tc = svc.create_lora_training_client(base_model=BASE, rank=32)
    tok = tc.get_tokenizer()

    # ---- baseline: the SAME base model, before any training
    baseline = evaluate(tc.save_weights_and_get_sampling_client(name="baseline"), tok, held, "baseline")

    # ---- build datums, count tokens so the cost is not a guess
    datums, train_tokens = [], 0
    for row in train:
        p = render(tok, row["note"])
        c = tok.encode(row["reply"] + tok.eos_token if getattr(tok, "eos_token", None) else row["reply"])
        full = list(p) + list(c)
        n_prefix = len(p) - 1
        train_tokens += len(full) - 1
        datums.append(types.Datum(
            model_input=types.ModelInput.from_ints(tokens=full[:-1]),
            loss_fn_inputs=dict(
                target_tokens=np.array(full[1:], dtype=np.int64),
                weights=np.array([0.0] * n_prefix + [1.0] * (len(full) - 1 - n_prefix), dtype=np.float32),
            )))

    print(f"examples={len(datums)} train_tokens_per_epoch={train_tokens} "
          f"epochs={EPOCHS} estimated_train_cost_usd={EPOCHS * train_tokens * 0.44 / 1e6:.4f}")

    for epoch in range(EPOCHS):
        fwdbwd = tc.forward_backward(datums, "cross_entropy")
        optim = tc.optim_step(types.AdamParams(learning_rate=LR))
        fwdbwd.result()
        optim.result()
        print(f"epoch {epoch + 1}/{EPOCHS} done")

    after = evaluate(tc.save_weights_and_get_sampling_client(name="steady-sft"), tok, held, "fine-tuned")

    report = {"base_model": BASE, "examples": len(datums), "epochs": EPOCHS,
              "train_tokens_per_epoch": train_tokens, "baseline": baseline, "fine_tuned": after}
    (HERE / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("base_model", "examples", "epochs",
                                             "train_tokens_per_epoch")}, indent=2))
    print(f"used_detail: baseline {baseline['used_detail_pct']}% -> "
          f"fine-tuned {after['used_detail_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
