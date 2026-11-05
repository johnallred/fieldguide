---
title: Screencasts and video
summary: "A screencast script is a code sample with timestamps, so it can be tested; the recording cannot be fixed, which is the whole cost of the medium."
diataxis: how-to
audience: developer
concept: screencasts
tags: [edu, context]
---

# Screencasts and video

`context` · difficulty 2 · 4h

!!! quote "Adjacent, not quoted"
    Neither posting mentions video. A common secondary deliverable in developer-relations roles.

**Prerequisites:** [Designing tutorials](tutorial-design.md)

## What it is

A recording of someone doing the thing, usually narrated. It is the only
documentation format where the reader can see tacit detail: which pane the
output appeared in, how long the build actually took, what the error looked
like before it was tidied into a code block.

It is also the only format in this guide that cannot be diffed, searched by
phrase, copy-pasted from, link-checked, or corrected without being remade. Each
of those is a property the rest of a docs-as-code toolchain depends on, so a
screencast sits outside every mechanism described elsewhere here, which is the
reason this concept is tier `context` rather than core.

## Why the job asks for it

Because some things genuinely do not survive being written down, and because
people ask for video regardless.

The legitimate case is narrow and real: an unfamiliar interface where the hard
part is knowing where to look, a workflow whose shape only becomes obvious when
you watch someone move through it, or a result so visual that describing it is
absurd. For those, thirty seconds of video beats a page.

The illegitimate case is more common. Video is requested because it feels more
approachable, produced because it is satisfying to make, and watched by far
fewer people than a page, having cost ten times as much and become wrong within
a quarter with nothing to detect it. That failure is not a reason to refuse;
it is a reason to build the half of the artifact that can be maintained.

## The golden path

Treat the script as code and test it, then watch the recording become wrong
anyway. About twenty-five minutes, and the second half is the point.

Committed as `drills/screencast_script.py`, which walks all three states in one
run. A test asserts it still prints the lines quoted below.

**Step 1: the script as a structured artifact**

Not a document. A list of beats, each with what is said, what is run, and what
appears:

```yaml
title: Listing your widgets
beats:
  - at: "00:12"
    say: "First we list the widgets, and you should see three of them."
    run: "python3 widget.py"
    expect: "widgets: 3"
  - at: "00:41"
    say: "Now the same thing as JSON."
    run: "python3 widget.py --json"
    expect: '{"widgets": 3}'
```

The `at` field is what makes this worth doing. Everything else is an ordinary
[validated code sample](code-sample-validation.md); the timestamp is what turns
a failure into an instruction about which four seconds of video are wrong.

**Step 2: test it like a code sample, because that is what it is**

```python
for beat in script["beats"]:
    r = subprocess.run(beat["run"].split(), capture_output=True, text=True, timeout=30)
    if beat["expect"] not in r.stdout.strip():
        bad.append(f'  {beat["at"]}  expected {beat["expect"]!r}, got {r.stdout.strip()!r}')
```

```
DRIFT  00:41  expected '{"widgets": 3}', got 'widgets: 3'
1/2 beats still match what the video shows
exit=1
```

The second beat was never true. The `--json` flag the narration describes did
not exist, and the script was written from what the author expected the tool to
do. Had this gone to recording, the video would have shown a narrator
confidently describing output nobody can reproduce.

That is the cheapest and most common video defect, and twenty lines of
script-checking catches it before the microphone is switched on.

**Step 3: implement the flag, and get a clean run**

```
2/2 beats still match what the video shows
exit=0
```

Now the recording would be accurate. Record it, publish it, move on.

**Step 4: upstream changes the output, as upstream does**

```bash
sed -i 's/print("widgets: 3")/print("3 widgets found")/' widget.py
```

```
DRIFT  00:12  expected 'widgets: 3', got '3 widgets found'
1/2 beats still match what the video shows
exit=1
```

Twelve seconds in, the video shows output the tool no longer produces. The
check caught it the next time CI ran, which is exactly what you want, and now
compare what that detection is worth in each medium:

| | A page | A screencast |
|---|---|---|
| What is wrong | Three characters | Four seconds of footage |
| Cost to fix | An edit | Re-record, or re-record everything after it |
| Until then | Fix it in the next commit | It is live and wrong |
| Reader's experience | None | Follows along, output differs, loses confidence |

The detection is the same. The remedy is not, and the asymmetry is the entire
argument about when to use video.

**Step 5: what the checked script actually buys**

Three things, none of which is a corrected video:

It stops wrong recordings being made, which is where most of the value is. It
tells you, by timestamp, exactly which recordings are now stale and how badly,
so a stale-video audit becomes a report rather than an afternoon of watching
your own back catalogue. And it is a text artifact: searchable, diffable,
and the thing you publish next to the video so that readers who want to copy a
command, or skim in forty seconds, can.

**Step 6: the measurement that decides this for a corpus**

```
pages with code:  106
fenced blocks:    727
lines of code and output: 9982
```

Every one of those 727 blocks is checked: it renders as code, its structure is
validated, and the samples with assertions are executed. The equivalent video
corpus would have nine thousand lines of commands with nothing checking any of
them, and no way to fix one without re-recording.

A screencast collection is only maintainable at a size where you are willing
to re-record it. That number is small, and knowing it before you start is the
difference between a useful handful of videos and a back catalogue nobody dares
audit.

**What you built.** A script format that tests like a code sample, a drift
check that reports by timestamp, two caught defects (one before recording and
one after), and a clear-eyed account of what detection is worth in a medium you
cannot patch.

## Reference

### What video is actually better at

| Situation | Why video wins |
|---|---|
| An unfamiliar GUI | Knowing where to look is the hard part |
| The shape of a workflow | Sequence and rhythm do not survive prose |
| A visual result | Describing it is absurd |
| Convincing someone it is easy | Watching someone succeed is persuasive |
| A conference talk recording | The artifact already exists |

Everything else is a page that someone wanted to be a video.

### What video cannot do

| Property | Consequence |
|---|---|
| Not searchable by phrase | Invisible to readers who search, and to retrieval |
| Not copy-pasteable | Viewers retype commands and mistype them |
| Not diffable | No review, no history of what changed |
| Not link-checkable | A URL on screen rots silently |
| Not patchable | A three-character fix means re-recording |
| Not skimmable | No way to find the one part you need |
| Not [agent-readable](agent-ready-content.md) | Absent from every retrieval pipeline |

The last row is newly expensive. A corpus whose answers live in video is a
corpus an assistant cannot answer from, which in practice means those answers
have stopped existing.

### The companion-text rule

Every screencast ships with a text twin: the commands, the expected output,
and the narration's substance. It costs little once the script exists in the
format above, and it is what makes the video findable at all, since in practice
the page is what people arrive at and the video is what some of them play.

| Artifact | Maintained | Found by search | Copy-pasteable |
|---|---|---|---|
| Video alone | No | Barely | No |
| Video plus auto-transcript | No | Poorly | No |
| Video plus checked script | The script is | Yes | Yes |

### Production decisions that matter, briefly

| Decision | Default |
|---|---|
| Length | Under four minutes, or chapter it |
| One task per video | Yes; compilations get abandoned partway |
| Show the failure | Yes, briefly; it is the tacit knowledge video is for |
| Terminal size and font | Large enough for a phone, which is where it is watched |
| Narration | Scripted; unscripted costs more in edit than it saves |
| Captions | Always, and they double as the transcript |

### When to refuse

| Request | Better answer |
|---|---|
| "Can we have a video of the quickstart?" | Fix the quickstart |
| "A video series for the whole product" | One video, then count plays |
| "Video because the docs are confusing" | The confusion will be in the video too |
| "Record the workshop and publish it" | Publish the handout; the recording is three hours long |

The third row is the one worth saying out loud in a planning meeting. Video
does not fix unclear material, it embeds it in a format you cannot edit.

## How to talk about it

**Lead with the asymmetry.** "A screencast script is a code sample with
timestamps, so I test it in CI like any other sample. What that buys is not a
corrected video: a three-character change to a tool means four seconds of
footage are wrong, and the fix is re-recording. The detection is identical to a
page's and the remedy is not, which is the whole argument about when video is
worth it."

**The follow-up is what the checking caught.** Two things, and the order
matters. Before recording, a beat whose narration described a flag that did not
exist, which is the commonest video defect and is free to catch. After
recording, an upstream output change twelve seconds in, which the check flagged
by timestamp, so a stale-video audit is a report instead of an afternoon
rewatching your own back catalogue.

**The scale point.** My corpus has 727 code blocks over 9,982 lines, all
checked. A video corpus of that size would have nothing checking any of it and
no way to fix one line. Screencasts are maintainable only at a size you are
willing to re-record, that number is small, and deciding it before you start is
what separates a useful handful from a back catalogue nobody dares audit.

**The tradeoff to volunteer.** I am sceptical of video and it does win
sometimes: an unfamiliar interface where knowing where to look is the hard
part, or a workflow whose shape does not survive prose. For those, thirty
seconds beats a page. What I would not do is answer "the docs are confusing"
with a video, because the confusion ends up in the video too, in a format
nobody can edit.

**One sharper point.** Video is now absent from retrieval. A corpus whose
answers live in recordings is one an assistant cannot answer from, and since
that is increasingly how people reach documentation, those answers have
effectively stopped existing. The companion text is no longer a courtesy.

## How to prove it

**The artifact.** A script format with timestamps, expected output and
narration, plus a CI job that runs every beat and reports drift by timestamp.

**Three things to do, in order:**

1. Take your most-watched screencast and run its commands by hand. Predict
   first whether they still produce what the video shows; the prediction is the
   exercise.
2. Write the script for your next video in the beats format and run the checker
   before recording anything. Step 2 above caught a narration describing a flag
   that did not exist, which is the defect this prevents for free.
3. Count the videos you currently publish and ask honestly whether you would
   re-record all of them for a three-character output change. The number you
   would re-record is the number you should maintain.

**What makes it credible rather than decorative.** The script checker above was
executed, caught a beat that was never true, passed cleanly after the flag was
implemented, and caught the upstream output change by timestamp; the corpus
figures of 727 blocks and 9,982 lines come from this guide's own pages. What
does not exist is a screencast: no video has been recorded, so the production
guidance is conventional practice rather than measured, and the
[demonstrated](../demonstrated.md) page records screencasts as having no
demonstration in either repository.

## Related

- [Designing tutorials](tutorial-design.md), the structure a script borrows
- [Code-sample validation](code-sample-validation.md), the mechanism step 2 reuses
- [Workshops and hands-on labs](workshops.md), the synchronous version of the same material
- [Agent-ready content](agent-ready-content.md), why the companion text now matters more
- [Freshness monitoring](freshness-monitoring.md), where a stale-video report belongs
