# I built a panic button that doesn't tell me anything

When someone close to you is getting through an addiction, you become the monitor. You ask how
it went. You check in. You want the number. It feels like support for about a week — and then it
is surveillance, and the moment honesty costs something, honesty stops. Which leaves you worse
off than when you started, because now the person you were trying to help has to manage your
feelings on top of their own.

This is my entry for the **Hacktoberfest Weekend Challenge**. The prompt is *open-source AI at
its core* — an open-weight model, an open-source harness, or local inference. The theme is
**Build for a Friend**: pick one real person and build something for them.

I built this for one real person: someone close to me who is getting through this, and I'm the
person closest to it. I'm deliberately not describing her, and not describing the specifics.
That's her information, and a repo is permanent.

So the thing I built is deliberately incomplete. It's called **Steady**, and its central design
decision is an *absence*.

## What it does

One screen, three buttons, sized for a phone at 3am:

- **"I'm having a craving right now"** — an open-weight model replies with one grounding line and
  one concrete thing to do in the next two minutes. No typing, no explaining, no waking anyone.
- **"The craving has passed"** — it marks the moment, so surviving becomes something you remember
  doing instead of something that only ever felt unsurvivable.
- **"I slipped"** — private. It does not report. It helps you work out what you want to say, to
  whom, and when.

## What it deliberately refuses to do

**The person supporting you gets a signal, never a transcript.** If she turns it on, all I would
ever see is something like *"she's gone quiet for a bit."* Never what she wrote, never how bad it
got, never whether she slipped.

**Steady keeps no session log.** Not "we don't look at it" — there is nothing to look at. A tool
that recorded this would be used dishonestly within a week, because that is what people do when
the record is a threat.

I want to be precise about why this isn't a compromise I'm grudgingly making. The whole value of
the tool *to me* is the refusal. If she doesn't trust the button, she won't press it, and the
button is worth nothing. **Privacy wasn't the ethical tax on this project. It's the mechanism.**

## The open-source AI core

Both model paths are open-weight, and there is no proprietary-model path in the code:

- **Gemma**, served through Google AI Studio — this entry also goes in the Gemma category.
- **A GGUF served locally by `llama.cpp`** — fully offline, no network at all.

And the model does not run on anyone's laptop. It runs in **GitHub Actions**, on a clean public
runner, from a workflow in the repo. The runner downloads the official GGUF, checksums it, runs
the support policy and uploads the reply as an artifact. **No API key, nothing installed on the
phone, and anyone can click the workflow and reproduce it.**

The policy lives in plain sight in `agent/steady.py`: no diagnosis, no dosages, no clinical
claims, replies under 60 words, at most one question, and an explicit rule never to moralise
about a slip.

Ask it for help with no model reachable and it does not improvise — it says so and hands over a
crisis pointer. I'd rather it be visibly broken than confidently wrong to someone mid-craving.

## Prize Categories

**Best Use of Gemma — featured.** Steady's model is Gemma, open-weight, and there is no
proprietary-model path anywhere in the code. It runs as an official Gemma GGUF served by
`llama.cpp`, fetched and checksummed by the workflow on every run.

**Best Use of GitHub Copilot — partner.** The qualifying path here is *"automate your project
with GitHub Actions,"* and for Steady that isn't a garnish: the entire model runtime **is** a
GitHub Actions workflow. Nothing runs on anyone's machine, and every run is public.

There is one family of categories Steady is built to lose — the data-layer ones (MongoDB Atlas,
Tiger Data). **Not keeping the data is the product.** A version of this that stored every craving
and every slip so it could win a storage prize would be the exact thing it exists to avoid.

## What I got wrong, in public

I built the model path four times, and the last failure was the most useful one.

`gemma-3-270m-it` — the smallest Gemma — **restated my instructions back at me** instead of
answering: *"Okay, I understand. I will adhere to the rules and provide a concise, helpful
response."* Useless to someone mid-craving. I moved to 1B, then 4B.

The 4B was warm and stayed inside the policy, **and it ignored her completely.** I passed it
*"walked past the shop and it hit hard"* and it never once mentioned the shop — every run it
offered breathing. I added a rule that ignoring what she said counts as a failure, and found a
real interface bug behind it: **I had been burying her words inside a paragraph of instructions
addressed to the agent.** Her sentence was a footnote in my message. I fixed that — her words are
now the user turn and nothing else — and **the behaviour still didn't change.**

That's when I stopped blaming the prompt and admitted it was capacity. A 4B model doesn't have
the room to hold the policy, her sentence, and a reply that uses both. So I moved to 12B:

> *"That walk brought it on strong. Feel your feet on the ground. Can you take three slow, deep
> breaths now?"* — using **her** word, from **her** sentence.

And then the bigger model did something worse. On its first run, given the same note, it said
*"That smell is strong right now."* **There was no smell.** It invented a sensory detail she never
gave and handed it to someone in distress as fact. So I added a rule that it may use only what
she actually said, and it stopped.

**Every step up the ladder bought capability and sold a little accuracy — and accuracy is the only
thing that matters here.** All four runs are public in the repo's Actions tab, failures included.
You can watch me get it wrong, watch the model invent something, and watch me take it back out.

## Honest limits

**Steady is not treatment.** Not therapy, not medical advice, not a crisis service. It cannot
detect anything or measure anything, and it doesn't replace a professional. If someone is in
immediate danger they should contact local emergency services, or find a verified crisis line for
their country at findahelpline.com.

And the CI round-trip takes tens of seconds, which is wrong for a 3am button. The workflow is the
reproducible proof that the open-weight path works. The phone UI is what someone would actually
press, pointed at a model they host themselves.

## What I'd say to anyone building for someone real

The constraint they give you *is* the product. Mine was one sentence — *"don't make me report to
you"* — and the whole design fell out of it. Everything I was tempted to add (history, streaks, a
dashboard for the supporter) would have quietly turned it back into the thing it exists to avoid.

Not every feature you can build is a feature you should ship to someone you love.
