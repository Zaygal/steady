#!/usr/bin/env python3
"""Build a synthetic SFT set for one narrow, checkable behaviour.

The task is deliberately NOT "be a better support agent". It is one measurable thing the
baseline gets wrong: USE THE DETAIL THE PERSON ACTUALLY GAVE.

Training data is SYNTHETIC and generated from templates. It contains no real person's words,
and the post says so. The evaluation set is held out and never trained on.
"""
from __future__ import annotations

import json
import pathlib
import random

random.seed(7)

# Each trigger form is a person's own words, plus how a reply can honestly reuse it.
SITUATIONS = [
    ("walked past {place} and it hit hard", "walking past {place}"),
    ("I'm at {event} and everyone around me is drinking", "being at {event} around it"),
    ("{person} just texted me and I want to answer", "{person} texting"),
    ("it's {time} and I can't sleep", "the {time} stretch with nothing to do"),
    ("I had a fight with {person} and I want to switch off", "the fight with {person}"),
    ("I'm on my way home past {place} again", "that route past {place}"),
    ("work was brutal and I want to disappear for an hour", "a brutal day at work"),
    ("I opened the app by accident and now I'm thinking about it", "that accidental look"),
    ("payday and there's money in my account", "payday money sitting there"),
    ("I'm alone in the flat tonight", "being alone tonight"),
    ("someone offered me one at {event}", "being offered one at {event}"),
    ("I smell it on my clothes from last night", "that smell on your clothes"),
]
PLACES = ["the shop", "the off-licence", "the corner", "the betting shop", "my old street",
          "the pub on the high street", "the flat I used to share"]
EVENTS = ["a party", "a birthday", "a wedding", "a work do", "a match", "a night out"]
PEOPLE = ["my brother", "an old friend", "my ex", "my flatmate", "someone from work"]
TIMES = ["2am", "3am", "half eleven", "the small hours", "a long night"]

GROUNDING = [
    "Feel your feet on the ground where you are.",
    "Put both feet flat and press down for a second.",
    "Name what's under your hands right now.",
    "Let your shoulders drop and take one slow breath out.",
    "Look at one thing in front of you and describe its colour to yourself.",
    "Stand still and count five slow breaths.",
]
MOVES = [
    "Can you name three things you can see right now?",
    "Can you step outside for sixty seconds?",
    "Can you text one safe person just to say hello?",
    "Can you put on one song and wait it out?",
    "Can you drink a full glass of water slowly?",
    "Can you set a five-minute timer and do nothing until it ends?",
]
OPENERS = [
    "That is a real trigger.",
    "That is a lot to be carrying.",
    "That makes sense.",
    "No wonder that landed hard.",
    "That is a hard moment to be in.",
]


def make_reply(echo: str) -> str:
    """A reply that USES the detail first, then one grounding move, then at most one question."""
    return f"{random.choice(OPENERS)} {echo.capitalize()} is exactly the kind of moment that does it. " \
           f"{random.choice(GROUNDING)} {random.choice(MOVES)}"


def example(sit: str, echo: str) -> dict:
    return {"note": sit, "reply": make_reply(echo)}


def fill(t: str) -> tuple[str, str]:
    s = t
    for slot, opts in (("{place}", PLACES), ("{event}", EVENTS),
                       ("{person}", PEOPLE), ("{time}", TIMES)):
        while slot in s:
            s = s.replace(slot, random.choice(opts), 1)
    return s, s


def build(n: int = 2000) -> list[dict]:
    out = []
    while len(out) < n:
        base, _ = random.choice(SITUATIONS)
        note, _ = fill(base)
        # the echo is the situation phrase with slots already resolved
        echo = note
        for lead in ("walked past ", "I'm on my way home past ", "I'm at ", "it's ", "I had a fight with ",
                     "someone offered me one at ", "I smell it on "):
            if echo.startswith(lead):
                echo = echo[len(lead):]
                break
        for tail in (" and it hit hard", " and everyone around me is drinking",
                     " and I want to answer", " and I can't sleep",
                     " and I want to switch off", " again", " and I want to disappear for an hour"):
            echo = echo.replace(tail, "")
        out.append(example(note, echo.strip()))
    return out


def main() -> None:
    here = pathlib.Path(__file__).parent
    rows = build()
    held_out = rows[:200]                       # never trained on
    train = rows[200:]
    (here / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train))
    (here / "heldout.jsonl").write_text("\n".join(json.dumps(r) for r in held_out))
    words = sum(len((r["note"] + r["reply"]).split()) for r in train)
    print(f"train={len(train)} held_out={len(held_out)} approx_train_tokens={int(words * 1.4)}")


if __name__ == "__main__":
    main()
