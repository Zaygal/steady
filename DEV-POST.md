# DEV post draft — Hacktoberfest Weekend Challenge, "Build for a Friend"

> Post this from your own DEV account at dev.to/new. Don't paste the draft wholesale —
> read it once so it sounds like you. Target 600-900 words. Tag it with the challenge.

---

## I built my partner a panic button that doesn't tell me anything

When two people are getting through the same thing together, one of you becomes the monitor.
You start asking how it went, checking in, wanting the number. It feels like support for about
a week. Then it is surveillance — and the moment honesty costs something, honesty stops.
Which means the person who wanted to help has now made it harder for the truth to reach them.

I built for one real person: my partner. We're getting through an addiction together. I'm not
going to describe her, and I'm not describing the details — that part is hers, and a repo is
permanent.

So the thing I built for her is deliberately incomplete. It's called **Steady**, and its
central design decision is an *absence*.

### What it does

One screen, three buttons, sized for a phone at 3am:

- **"I'm having a craving right now"** — an open-weight model responds with one grounding line
  and one concrete thing to do in the next two minutes. No typing required, no explaining,
  no waking anyone.
- **"The craving has passed"** — it marks the moment, so surviving it becomes a memory she can
  reuse instead of a thing that only ever felt unsurvivable.
- **"I slipped"** — private. It does not report. It helps her work out what she wants to say,
  to whom, and when. Punished honesty is dishonest honesty.

And then the part that matters most:

### What it deliberately refuses to do

**The partner gets a signal, never a transcript.** If she turns it on, all I would ever see is
something like *"she's gone quiet for a bit."* Never what she wrote, never how bad it got,
never whether she slipped.

**Steady keeps no session log.** Not "we don't look at it" — there is nothing to look at.
A tool that recorded this would be used dishonestly within a week, because that is what
people do when the record is a threat.

I want to be precise about why this isn't a compromise I'm making. The whole value of the tool
to *me* is the refusal. If she doesn't trust the panic button, she won't press it, and the
button is worthless. Privacy wasn't the ethical tax on this project; it is the mechanism.

### The open-source AI core

Both model paths are **open-weight**, and there is no proprietary-model path in the code:

- **Gemma, served through Google AI Studio** (this entry also goes in the Gemma category).
- **A GGUF model served locally by `llama.cpp`** — fully offline, no network.

The support policy lives in plain sight in `agent/steady.py`: no diagnosis, no dosages, no
clinical claims, replies under 60 words, at most one question, and an explicit rule never to
moralise about a slip. The open pieces are what make it work — swap the model, keep the policy.

### Where it fails loudly

Ask it for help with no model reachable and it does not improvise. It says so, and it hands
over a crisis pointer. I'd rather it be visibly broken than confidently wrong to someone
mid-craving.


### What I got wrong, in public

I built the model path three times.

`gemma-3-270m-it` — the smallest Gemma — **restated my instructions back at me** instead of
answering: *"Okay, I understand. I will adhere to the rules and provide a concise, helpful
response."* Funny, and useless to someone mid-craving. I moved up to 1B, then 4B.

The 4B is warm and stays inside the policy. But I passed it *"walked past the shop and it hit
hard"* and it never once mentioned the shop — every run, it offered breathing. I added an
explicit rule that ignoring the person's own words counts as a failure, and I found a real
interface bug behind it: **I had been burying the person's words inside a paragraph of
instructions addressed to the agent.** Their sentence was a footnote in my message. I fixed
that — their words are now the user turn and nothing else — and **the behaviour still didn't
change.**

I'm writing that down rather than leaving it out, because it's the honest cost of a model small
enough to run for free, and it's the first thing I'd spend more compute on. Every one of those
runs is public in the repo's Actions tab — you can watch me get it wrong.

The upside is real though: the model runs in CI on an open runner, from an open-weight GGUF,
served by `llama.cpp`, with **no API key and nothing installed on anyone's machine.**

### Honest limits

It is **not treatment**, not therapy, not a crisis service. It cannot detect anything or
measure anything. It is one small thing that works in the ten seconds that matter.

If you're building for someone real: the constraint they give you is the product. Mine was
"don't make me report to you," and the whole design fell out of that one sentence.
