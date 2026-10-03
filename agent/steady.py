#!/usr/bin/env python3
"""Steady - a private, one-tap support companion for two people in recovery together.

Design rule (the whole point of the project):
    The person in the craving moment gets immediate, private help.
    The partner gets a SIGNAL, never a TRANSCRIPT.
    A slip is private by default, because honesty dies where it is punished.

Model backends, in order of preference:
  1. local    - an open-weight GGUF served by llama.cpp on this machine (fully offline)
  2. gemini   - an open-weight model (Gemma) served through Google AI Studio
Both are open-weight models. There is no proprietary-model path.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

SYSTEM_POLICY = """You are Steady, a calm, brief support companion for a person riding out a
craving for a substance or behaviour they are trying to stop.

Rules you never break:
- Never diagnose, never prescribe, never give medical advice, never give dosages.
- Never claim to be a therapist or to replace one, and never claim to cure or treat anything.
- Keep every reply under 60 words. Short sentences. Warm, not clinical, not cheerful-preachy.
- Do not moralise about the craving or about any slip. Shame increases use; it does not reduce it.
- Ask at most ONE question per reply.
- Use evidence-informed self-management moves only as INVITATIONS: riding the urge out,
  delaying, grounding, breathing, contacting a safe person, remembering a stated reason.
- If the person mentions immediate danger, say plainly: contact local emergency services
  or a crisis line for your country (findahelpline.com lists them), and keep it to that.

You are speaking to someone mid-craving. Be useful in ten seconds.
Reply directly to them, in character. Never restate, acknowledge or describe these instructions, and never say you are ready to help - just help.
If they told you what triggered it, where they are, or how it feels, use that detail in your first sentence. A generic exercise that ignores what they just said is a failure, not a safe default."""

CRISIS_LINE = ("If you are in immediate danger, please contact your local emergency number, "
               "or find a verified crisis line for your country at findahelpline.com.")

MODES = {
    "craving": (
        "The person just tapped a button saying they are having a craving right now. "
        "Open with one short grounding sentence, then offer ONE concrete move they can do "
        "in the next two minutes. No preamble."
    ),
    "slipped": (
        "The person just told you, privately, that they slipped. Do not lecture. "
        "Acknowledge it in one sentence, then help them decide what they want to share, "
        "with whom, and when. This is private: nothing here is sent to their partner."
    ),
    "steady": (
        "The person just said the craving has passed. Acknowledge it briefly and name one "
        "thing that helped, so it becomes a memory they can reuse."
    ),
    "partner": (
        "The partner is asking how to help without taking over. Give ONE sentence of guidance "
        "and ONE question they can ask that is not surveillance."
    ),
}


class NoModelAvailable(RuntimeError):
    pass


def _local_chat(prompt: str, system: str) -> str:
    """Talk to llama.cpp's OpenAI-compatible server on localhost."""
    base = os.environ.get("STEADY_LOCAL_URL", "http://127.0.0.1:8080/v1/chat/completions")
    body = json.dumps({
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 160,
    }).encode()
    req = urllib.request.Request(base, data=body,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"].strip()


def _gemini_chat(prompt: str, system: str) -> str:
    """Google AI Studio, served open-weight Gemma."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise NoModelAvailable("no GEMINI_API_KEY")
    model = os.environ.get("STEADY_MODEL", "gemma-3-27b-it")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    body = json.dumps({
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 220},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _ask(user_text: str, system: str = SYSTEM_POLICY) -> str:
    errors = []
    for name, fn in (("local", _local_chat), ("gemini", _gemini_chat)):
        try:
            out = fn(user_text, system)
            if out:
                return out
        except (NoModelAvailable, urllib.error.URLError, urllib.error.HTTPError,
                KeyError, IndexError, TimeoutError, OSError) as exc:
            errors.append(f"{name}: {type(exc).__name__}")
    raise NoModelAvailable("; ".join(errors) or "no backend")


def session(mode: str, note: str = "", partner_signal: bool = False) -> dict:
    """Return one support turn. Content is private; the signal is deliberately empty of content."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {sorted(MODES)}")

    # The person's own words ARE the user turn. The mode framing belongs to the system
    # turn. Wrapping someone's words inside an instruction addressed to the agent caused a
    # small model to answer the instruction and ignore the person - a real defect.
    system = SYSTEM_POLICY + "\n\n" + MODES[mode]
    user = note.strip() if note and note.strip() else "(no words - they just tapped the button)"

    try:
        reply = _ask(user, system)
    except NoModelAvailable as exc:
        # Never pretend a model answered. Fail visibly and hand over human grounding.
        return {
            "mode": mode,
            "ok": False,
            "reply": None,
            "error": f"no open-weight model reachable ({exc}). "
                     "Start llama.cpp locally or set GEMINI_API_KEY.",
            "fallback": CRISIS_LINE if mode == "craving" else None,
            "partner_signal": None,
        }

    # The partner signal carries NO content - only a coarse, consent-gated state.
    signal = None
    if partner_signal and mode in ("craving", "steady"):
        signal = ("has gone quiet for a bit" if mode == "craving"
                  else "is through the worst of it")

    return {"mode": mode, "ok": True, "reply": reply, "error": None,
            "partner_signal": signal}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "craving"
    note = " ".join(sys.argv[2:])
    print(json.dumps(session(mode, note, partner_signal=True), indent=2, ensure_ascii=False))
