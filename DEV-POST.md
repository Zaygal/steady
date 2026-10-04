---
title: I built a panic button that doesn't tell me anything
published: 
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

When someone close to you is getting through an addiction, you become the monitor. You ask how it
went. You check in. You want the number. It feels like support for about a week — and then it is
surveillance, and the moment honesty costs something, honesty stops. Which leaves you worse off
than when you started, because now the person you were trying to help has to manage your feelings
on top of their own.

I built this for one real person: someone close to me who is getting through this, and I'm the
person closest to it. I'm deliberately not describing her, and not describing the specifics.
That's her information, and a repo is permanent.

## What I Built

**Steady** — one screen, three buttons, sized for a phone at 3am.

- **"I'm having a craving right now"** — an open-weight model replies with one grounding line and
  one concrete thing to do in the next two minutes. No typing, no explaining, no waking anyone.
- **"The craving has passed"** — it marks the moment, so surviving becomes something you remember
  doing instead of something that only ever felt unsurvivable.
- **"I slipped"** — private. It does not report. It helps you work out what you want to say, to
  whom, and when.

But the thing I actually built is an absence.

**The person supporting you gets a signal, never a transcript.** If she turns it on, all I would
ever see is something like *"she's gone quiet for a bit."* Never what she wrote, never how bad it
got, never whether she slipped.

**Steady keeps no session log.** Not "we don't look at it" — there is nothing to look at. A tool
that recorded this would be used dishonestly within a week, because that is what people do when
the record is a threat.

I want to be precise about why this isn't a compromise I'm grudgingly making. The whole value of
the tool *to me* is the refusal. If she doesn't trust the button, she won't press it, and the
button is worth nothing. **Privacy wasn't the ethical tax on this project. It's the mechanism.**

## Demo

Live at **https://steady-21e1.onrender.com** — open it on a phone. Type something, or nothing, and
tap a button.

![Steady answering with her own words, and the signal her partner would see instead of a transcript](https://raw.githubusercontent.com/Zaygal/steady/main/docs/demo-2-reply.png)

That screenshot is a real reply, word for word:

> *"Walking past that shop is a lot to handle. Can you try to name five things you can see right
> now to help ground yourself?"*
>
> — your partner would see only: *"she has gone quiet for a bit."*

That second line is the entire design on one screen. She gets the help. He gets a signal with no
content in it. Nobody had to decide whether to be honest.

**Honest performance note:** a reply takes **40–80 seconds**, because Gemma 4 reasons before it
answers. The service itself is always-on now — no cold start — but that latency is the model's,
not the box's, and it is far too slow to be a real 3am button. Which is exactly why the path
below runs on your own device instead.

## Code

{% embed https://github.com/Zaygal/steady %}

**https://github.com/Zaygal/steady** — MIT, and deliberately small. `agent/steady.py` is the whole
policy and the model calls. `app/server.py` is a stdlib HTTP server with **no third-party
dependencies at all** — a support tool for someone in crisis should have the smallest possible
attack surface. `app/index.html` is the entire front end. `NOT-A-TREATMENT.md` is a thing I
shouldn't have to write, and did.

## How I Built It

Both model paths are open-weight, and **there is no proprietary-model path in the code**:

- **Gemma**, served through Google AI Studio — `gemma-4-31b-it` answering on the live site.
- **A GGUF served locally by `llama.cpp`** — fully offline, no network at all.

And the model does not run on anyone's laptop. It runs in **GitHub Actions**, on a clean public
runner, from a workflow in the repo. The runner downloads the official GGUF, checksums it, runs the
support policy and uploads the reply as an artifact. **No API key, nothing installed on the phone,
and anyone can click the workflow and reproduce it.**

The policy lives in plain sight in `agent/steady.py`: no diagnosis, no dosages, no clinical claims,
replies under 60 words, at most one question, and an explicit rule never to moralise about a slip.
Ask it for help with no model reachable and it does not improvise — it says so and hands over a
crisis pointer. I'd rather it be visibly broken than confidently wrong to someone mid-craving.

## Why Does Open Innovation Matter?

I could have built this on a proprietary model behind an API key. I didn't, and the reasons are
specific to this problem rather than general praise for open source.

**A tool about addiction has to be inspectable.** Someone is being asked to trust it in the worst
hour of their week, so "nothing is kept" cannot be a marketing line — it has to be checkable. The
entire policy is thirty lines in `agent/steady.py`. The model is a public GGUF. The runtime is
`llama.cpp`. The workflow that runs it is in the repo. You can read all of it, and none of it
required my permission.

**Free matters more here than anywhere.** A person in a bad week is not going to add a subscription
to get help at 3am. Open weights mean they can run this on hardware they already own, indefinitely,
without a billing relationship deciding whether they deserve an answer.

**Swappable means it outlives me.** The model is one environment variable. When a better small model
lands — and it will — nobody needs my release cycle, or my continued existence, to put it in. That's
the difference between an open project and a product I own.

## My Agent Session

DevRelay sessions are optional, so here's the equivalent: **every run of the agent is public in the
[Actions tab](https://github.com/Zaygal/steady/actions)**, including the four that went wrong. That
tab is the actual build log, and it's more candid than a summary would be.

## Prize Categories

**Best Use of Render — featured.** The front end is live on Render at
**https://steady-21e1.onrender.com**. The criterion is *"host an agent's front end,"* and you can
open it on a phone right now.

**Best Use of Gemma — featured.** Gemma is the model, open-weight, with no proprietary path
anywhere. The app asks the API which open-weight Gemma ids the key can actually reach instead of
trusting a hardcoded id — which is how I found that this key serves **Gemma 4**, not the Gemma 3
ids I had assumed, all of which returned 404.

**Best Use of GitHub Copilot — partner.** The qualifying path is *"automate your project with
GitHub Actions,"* and for Steady that isn't a garnish: the entire model runtime **is** a GitHub
Actions workflow. Nothing runs on anyone's machine, and every run is public.

There's one family of categories Steady is built to lose — the data-layer ones (MongoDB Atlas,
Tiger Data). **Not keeping the data is the product.** A version that stored every craving and every
slip so it could win a storage prize would be the exact thing it exists to avoid.

## What I Got Wrong, in Public

I built the model path four times, and the last failure was the most useful one.

`gemma-3-270m-it` — the smallest Gemma — **restated my instructions back at me** instead of
answering: *"Okay, I understand. I will adhere to the rules and provide a concise, helpful
response."* Useless to someone mid-craving. I moved to 1B, then 4B.

The 4B was warm and stayed inside the policy, **and it ignored her completely.** I passed it
*"walked past the shop and it hit hard"* and it never once mentioned the shop — every run it offered
breathing. I added a rule that ignoring what she said counts as a failure, and found a real
interface bug behind it: **I had been burying her words inside a paragraph of instructions addressed
to the agent.** Her sentence was a footnote in my message. I fixed that — her words are now the
user turn and nothing else — and **the behaviour still didn't change.**

That's when I stopped blaming the prompt and admitted it was capacity. A 4B model doesn't have the
room to hold the policy, her sentence, and a reply that uses both. So I moved to 12B:

> *"That walk brought it on strong. Feel your feet on the ground. Can you take three slow, deep
> breaths now?"* — using **her** word, from **her** sentence.

And then the bigger model did something worse. On its first run, given the same note, it said
*"That smell is strong right now."* **There was no smell.** It invented a sensory detail she never
gave and handed it to someone in distress as fact. So I added a rule that it may use only what she
actually said, and it stopped.

**Then I tried to fix it with a fine-tune, and that failed too.** I trained a LoRA adapter on
1,800 synthetic examples and compared it against the same model untuned, on a held-out set, against
one metric I fixed *before* running it: does the reply reuse a content word from the person's note?

> baseline **68.3%** → fine-tuned **60.0%**, for $1.11

It made it worse. So there is no "Best Use of Tinker" claim anywhere in this post — I'm not going to
go shopping for a metric that flatters my own adapter. What the samples actually show is that my
*metric* was the weak part: the baseline learned to parrot her sentence straight back, which
guarantees word overlap and reads like a machine, while the fine-tuned model used the exact noun the
baseline had paraphrased away. Two real lessons: the defect I'd documented was the **4B's capacity
limit, not a universal problem** — a 30B model already used the detail 68% of the time — and my
synthetic data was too mechanical to beat that.

**Every step up the ladder bought capability and sold a little accuracy — and accuracy is the only
thing that matters here.** All four runs are public. You can watch me get it wrong, watch the model
invent something, and watch me take it back out.

## Honest Limits

**Steady is not treatment.** Not therapy, not medical advice, not a crisis service. It cannot detect
anything or measure anything, and it doesn't replace a professional. If someone is in immediate
danger they should contact local emergency services, or find a verified crisis line for their
country at findahelpline.com.

The instance is always-on, so there is no cold start. The workflow is the reproducible proof that
the open-weight path works; the phone UI is what someone would actually press, pointed at a model
they host themselves.

## What I'd Say to Anyone Building for Someone Real

The constraint they give you *is* the product. Mine was one sentence — *"don't make me report to
you"* — and the whole design fell out of it. Everything I was tempted to add (history, streaks, a
dashboard for the supporter) would have quietly turned it back into the thing it exists to avoid.

Not every feature you can build is a feature you should ship to someone you love.
