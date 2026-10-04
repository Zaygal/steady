# Steady

A private, one-tap support companion for two people who are getting through something together.

Built for **one real person** — someone close to me — as an entry in the
[Hacktoberfest Weekend Challenge](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01),
theme *"Build for a Friend."* Her name and anything identifying her are deliberately not in
this repository. That is her information to publish, not mine.

## The problem this actually solves

When two people are getting through the same thing, the partner becomes the monitor. That
feels like help for about a week. After that it is surveillance, and once honesty is punished
the person stops reporting the truth — which is the one thing the partner needed.

So Steady inverts it:

- **In the craving moment**, the person taps one button and gets immediate, private help.
  No typing, no explaining, no waking anyone at 3am.
- **The partner gets a signal, never a transcript.** "She's gone quiet for a bit" — or nothing
  at all, if she hasn't opted in for that moment. The content never leaves the session.
- **A slip is private by default.** Steady helps you decide *what you want to say and to whom*,
  instead of auto-reporting it. Honesty has to be worth something.

**The absence of a transcript is the feature.** A tool that logged this would be used
dishonestly within a week.

## Open-source AI at its core

Two backends, both **open-weight** — there is no proprietary-model path in this code:

1. **Local, fully offline** — a GGUF model served by `llama.cpp` on your own machine.
2. **Gemma via Google AI Studio** — an open-weight model served through a provider;
   this also enters the challenge's Gemma category.

The support policy, the privacy inversion and the refusal to log are all in
[`agent/steady.py`](agent/steady.py) — the open pieces are what makes it work.

## Where the model actually runs

The open-weight model is **not downloaded to the user's machine and not called through a
proprietary API.** It runs in GitHub Actions, on a clean runner, from the workflow in
[`.github/workflows/steady-agent.yml`](.github/workflows/steady-agent.yml):

```bash
gh workflow run steady-agent.yml -f mode=craving -f note="walked past the shop"
gh run watch && gh run view --log
```

Model: **`gemma-3-270m-it` (Q8_0 GGUF)** from `ggml-org/gemma-3-270m-it-GGUF`, served by
**`llama.cpp`**. The runner downloads it, checksums it, runs the policy and uploads the reply
as an artifact — so the result is reproducible by anyone who clicks the workflow.

**Honest tradeoff:** a CI round-trip takes tens of seconds, which is wrong for a 3am panic
button. The workflow is the *reproducible proof* that the open-weight path works; the phone UI
is what someone would actually press, pointed at a model they host themselves.

## What the open-weight model actually does — real runs, all public

Every reply below came out of a GitHub Actions run on this repository. None of it is a mock-up.

| model | reply it produced |
|---|---|
| `gemma-3-270m-it` Q8_0 | *"Okay, I understand. I will adhere to the rules and provide a concise, helpful response..."* — it restated its own instructions instead of answering |
| `gemma-3-1b-it` Q4_K_M | *"The urge is present. Focus on your breath. Slow down. Take a deep breath in, hold for three seconds, and exhale slowly."* |
| `gemma-3-4b-it` Q4_K_M | *"That's alright. You're noticing the craving. Try a simple breathing exercise now. In for four, hold for four, out for six."* |
| `gemma-3-4b-it` Q4_K_M, after fixing the prompt shape | *"The feeling is present. Try a slow, deep breath now. In for four, hold for four, out for six."* |
| `gemma-3-12b-it` Q4_K_M | *"That smell is strong right now. Can you feel your feet on the ground?"* — **it used the trigger, then invented a smell she never mentioned** |
| `gemma-3-12b-it` Q4_K_M + the accuracy rule | *"That walk brought it on strong. Feel your feet on the ground. Can you take three slow, deep breaths now?"* — **uses only her own words** |

**The honest finding.** Passed the note *"walked past the shop and it hit hard"*, the small models
never used it — they defaulted to a generic breathing exercise every time. Two prompt fixes
changed nothing, because this was **capacity, not phrasing**: a 4B cannot hold the policy, her
sentence, and a response that uses both.

Moving to 12B fixed it, and then introduced something worse. The first 12B run answered the
trigger correctly but said *"That smell is strong right now"* — **there was no smell.** It invented
a sensory detail she never gave and handed it to someone in distress as fact. A rule that it may
use only the details she actually gave stopped it.

That is the real lesson of this repo, and it is not "use a bigger model": **every step up the
ladder bought capability and sold a little accuracy, and accuracy is the only thing that matters
here.**

## Run it

```bash
# 1. quickest - open-weight Gemma via Google AI Studio (free key)
export GEMINI_API_KEY=...           # https://aistudio.google.com/apikey
python3 agent/steady.py craving "walked past the shop, it hit hard"

# 2. fully local - no network at all
#    download a small open-weight GGUF and serve it with llama.cpp, then:
export STEADY_LOCAL_URL=http://127.0.0.1:8080/v1/chat/completions
python3 agent/steady.py craving
```

Phone-first UI:

```bash
python3 app/server.py     # then open http://<your-laptop-ip>:8765 on your phone
```

## What it does not do

It is **not treatment**, not therapy, not a crisis service, and it makes no clinical claim.
See [NOT-A-TREATMENT.md](NOT-A-TREATMENT.md). It cannot detect a slip, cannot measure
anything, and does not replace a professional.

## Build window

Started and completed inside the Hacktoberfest Weekend Challenge window (Oct 2-5, 2026).
Any commit after the deadline is listed here:

- (none yet)

## Licence

MIT.
