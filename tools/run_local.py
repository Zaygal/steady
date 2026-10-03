#!/usr/bin/env python3
"""Run the Steady support policy against a LOCAL open-weight model.

Imported policy, not a reimplementation: the system policy lives in agent/steady.py so
that the API path and the local path can never drift apart.
"""
from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "agent"))
import steady  # noqa: E402

GGUF = os.environ.get("STEADY_GGUF", "models/gemma-3-270m-it-Q8_0.gguf")
MODE = os.environ.get("MODE", "craving")
NOTE = os.environ.get("NOTE", "")


def main() -> int:
    if MODE not in steady.MODES:
        print(f"unknown mode {MODE!r}; expected one of {sorted(steady.MODES)}", file=sys.stderr)
        return 2

    if not pathlib.Path(GGUF).is_file():
        print(f"no model at {GGUF} - refusing to fake a reply", file=sys.stderr)
        return 1

    from llama_cpp import Llama

    llm = Llama(model_path=GGUF, n_ctx=2048, n_threads=2, verbose=False)

    system = steady.SYSTEM_POLICY + "\n\n" + steady.MODES[MODE]
    user = NOTE.strip() if NOTE.strip() else "(no words - they just tapped the button)"
    out = llm.create_chat_completion(
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        max_tokens=180, temperature=0.6,
    )
    print(out["choices"][0]["message"]["content"].strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
