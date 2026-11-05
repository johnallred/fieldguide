---
title: Real-time and graphics systems
summary: "The median completion time barely moved while the deadline miss rate went from zero to thirty per cent, and then the system fell off a cliff."
diataxis: explanation
audience: developer
concept: realtime-systems
tags: [dom, context]
---

# Real-time and graphics systems

`context` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Documentation experience in graphics, simulation, robotics, or real-time systems"

## What it is

Systems where being late is being wrong. A real-time system is not a fast
system; it is one with a **deadline**, and a result delivered after the
deadline has no value, or negative value. Graphics is the familiar case: a
frame that misses the display refresh is not a slightly slower frame, it is a
dropped frame, and the user sees a stutter rather than a delay.

That one property changes which numbers matter, and it is the thing documentation
in this domain most often gets wrong.

## Why the job asks for it

Because the metric conventions a documentation writer brings from web services
are actively misleading here, and NVIDIA lists four domains that all share this
property.

In a web service, a slow request is a degraded request and the mean is a
reasonable summary. In a real-time system, the mean is close to irrelevant: a
system that meets its deadline 99 per cent of the time and misses one per cent
has a one per cent failure rate, and the mean will look excellent either way.
Writing "average frame time 8 ms" about a 60 Hz target is technically true and
tells the reader nothing about whether their frames land.

## The golden path

Run the same work against tightening deadlines and watch the summary statistics
stay healthy while the system fails. About twenty-five minutes, pure Python, no
hardware.

**Step 1: a periodic task, and the work it does**

```python
for i in range(N):
    target = start + (i + 1) * period / 1000
    now = time.perf_counter()
    if target > now:
        time.sleep(target - now)
    sum(x * x for x in range(WORK))            # the work
    done.append((time.perf_counter() - target) * 1000)
```

```
the work itself: mean 2.068 ms per cycle
```

About two milliseconds of work. Now give it less and less room.

**Step 2: sweep the deadline**

One run, on a shared two-core cloud machine:

```
  period  misses        completion time (ms)
    (ms)              mean     p50     p99     max
    10.0     0/250    2.363   1.762   4.314   4.551
     5.0     0/250    1.702   1.521   3.108   4.332
     2.0    67/250    3.308   1.482  22.912  24.702
     1.5   250/250   39.945  42.665  47.797  49.909
```

Read the `p50` column down the first three rows: **1.762, 1.521, 1.482 ms.** It
does not rise. It improves.

Now read the miss column beside it: **0, then 0, then 67 of 250.**

**A quarter of deadlines missed, and the median is better than it was on the
row with no misses at all.** A dashboard plotting median completion time would
show a healthy, improving line. The mean rises from 2.4 to 3.3 ms, which nobody
pages anyone about. The columns that noticed are `p99`, which went to 22.9 ms,
fifteen times the median, and the miss count.

**Step 3: the numbers move, and the shape does not**

Repeating the sweep is itself instructive. At the 2 ms period, across six runs:

```
misses at period 2.0 ms:  67, 81, 164, 176, 202, 205  (of 250)
```

A factor of three, from nothing but what else the machine was doing. So the
specific counts above are one sample and not a property of the code, which is
worth saying before quoting any of them.

Three things were stable across every run:

```
a loose deadline (10 ms)   0 misses, always
a tight one (1 ms)         250/250, always
the median                 stayed between 1.4 and 4 ms throughout
```

The median never tracked the miss rate, in any run. That is the transferable
finding, and the variance is the second one: a general-purpose machine cannot
give a repeatable answer here, which is precisely why real-time work reaches
for a dedicated kernel, pinned cores and locked memory rather than better
averages.

**Step 4: the cliff**

Wherever the transition falls, it is not gradual:

```
  2.0 ms period:   67/250 missed,  p50  1.5 ms
  1.5 ms period:  250/250 missed,  p50 42.7 ms
```

Completion time goes from 1.5 ms to 42.7 ms, a factor of 28, for a 25 per cent
tightening of the deadline. Once the work cannot fit in the period, each cycle
starts late, so the next starts later, and lag compounds without limit. There is
no gentle region: the system is fine, then it is unrecoverable.

That is the characteristic failure shape of this whole domain, and it is why
headroom is discussed differently here. A web service at 80 per cent
utilisation is busy. A real-time system at 80 per cent utilisation is one
scheduling hiccup from the cliff.

**Step 5: what this means for the writing**

Three consequences, each a concrete documentation decision:

```
state the deadline, not the average      "16.6 ms at 60 Hz", never "fast"
publish the miss rate                    the mean cannot express failure
publish the tail, p99 and max            the mean hides a 15 ms max at p50 1.5
```

And one more that is easy to miss. In the run above, the work took 2.07 ms and
median completion at a 10 ms period was 1.76 ms, which looks impossible. They
are different statistics, a mean against a median, on a machine whose timings
vary by a factor of three. That is the lesson rather than a
footnote: on this hardware the overhead of being scheduled is not separable
from the noise, so any budget a page offers has to be stated with the margin
included and the measurement conditions named.

**What you built.** A deadline sweep showing a median that improves while a
quarter of deadlines are missed, a variance measurement showing the counts are
not reproducible, the cliff where lag starts compounding, and the things a page
in this domain has to publish instead of an average.

## Reference

### Hard, firm and soft

| Kind | A missed deadline | Example |
|---|---|---|
| Hard | System failure, possibly unsafe | Flight control, motor commutation |
| Firm | The result is worthless, no harm | A dropped video frame |
| Soft | Value degrades with lateness | A UI animation, a game's physics |

Most things called real-time are firm or soft. The distinction matters in
writing because it decides whether the correct advice is "guarantee it" or
"degrade gracefully", and those are different pages.

### Which numbers to publish

| Statistic | Says | Verdict here |
|---|---|---|
| Mean | Typical throughput | Nearly useless; see step 2 |
| Median | Typical experience | Actively misleading; it was flat at 30% misses |
| p99, p99.9 | The tail that fails | Essential |
| Max over a run | The worst case observed | Essential, and not a bound |
| Deadline miss rate | The failure rate | The number that matters |
| Jitter, max minus min | Predictability | Often the real requirement |
| Worst-case execution time | A provable bound | Hard systems only, and expensive |

A page that quotes a mean in this domain has chosen the one statistic that
cannot express the failure mode.

### Frame budgets, as the familiar case

| Refresh | Budget per frame |
|---|---|
| 30 Hz | 33.3 ms |
| 60 Hz | 16.6 ms |
| 90 Hz | 11.1 ms |
| 120 Hz | 8.3 ms |
| 144 Hz | 6.9 ms |

The budget covers everything: simulation, culling, draw submission, present,
and the scheduling overhead from step 4. Documentation that gives a per-feature
cost without saying what the budget is leaves the reader unable to add up.

### Why a general-purpose OS is not real-time

| Source of lateness | Typical scale |
|---|---|
| Scheduler granularity | Tens of microseconds to milliseconds |
| Another process being runnable | Unbounded |
| Page faults and memory allocation | Microseconds to milliseconds |
| Garbage collection, where present | Milliseconds, unpredictably |
| Interrupt handling | Microseconds |
| Frequency and thermal management | Milliseconds, and invisible |

Measured here: the same sweep gave between 67 and 205 deadline misses out of
250 across six runs, a factor of three from nothing but neighbouring load. A
page claiming a sub-millisecond guarantee on a stock kernel is claiming
something the kernel does not offer, and this is why real-time work reaches for
`PREEMPT_RT`, core pinning, locked memory and allocation-free hot paths.

### Terms worth recognising

| Term | Means |
|---|---|
| Jitter | Variation in timing, often worse than latency |
| Determinism | The same input gives the same timing |
| Priority inversion | A low-priority task blocking a high-priority one |
| Starvation | A task that never gets scheduled |
| Admission control | Refusing work to protect the deadline |
| Headroom | Unused capacity, which is the safety margin |
| WCET | Worst-case execution time, a proved upper bound |

### Things to put in a page in this domain

| Do | Instead of |
|---|---|
| State the deadline in milliseconds | "Real-time", "fast", "low latency" |
| Publish a miss rate | A mean |
| Give the tail and the max | A single number |
| Include scheduling overhead in budgets | Quoting the work alone |
| Say what degrades when the deadline is missed | Leaving the failure mode implicit |
| Name the required kernel or configuration | Implying stock hardware suffices |

## How to talk about it

**Lead with the definition, because it is the whole thing.** "A real-time
system is not a fast system, it is one with a deadline, and a result after the
deadline has no value. A frame that misses the refresh is not a slow frame, it
is a dropped frame. That changes which numbers mean anything."

**Then the measurement, which is the part worth bringing.** I ran a fixed piece
of work against tightening periods. At a 10 ms deadline, no misses and a median
of 1.76 ms. At 2 ms, sixty-seven misses out of 250 and a median of 1.48,
*better* than the row with no misses, while p99 went to 22.9 ms, fifteen times
the median. A quarter of deadlines missed and every summary statistic looking
healthy or improving.

**The second finding, which I would not have had without repeating it.** The
miss count at that period ranged from 67 to 205 across six runs, a factor of
three from neighbouring load alone. So the counts are not a property of the
code, and the transferable claim is the shape: the median never tracked the miss
rate in any run. The variance is itself the argument for why this domain uses
dedicated kernels and pinned cores rather than better averages.

**The third, which is about headroom.** Tightening the deadline by 25 per cent,
from 2 ms to 1.5, took it from sixty-seven misses to all 250 and the median from
1.5 ms to 42.7. Once the work does not fit, every cycle starts later than the
last and lag compounds, so there is no gentle region. That is why utilisation
reads differently here: 80 per cent in a web service is busy, and in a real-time
system it is one hiccup from the cliff.

**Be honest about the depth.** This is Python on a general-purpose kernel,
which is the right vehicle for showing why general-purpose kernels are not
real-time and the wrong one for anything else. No `PREEMPT_RT`, no GPU, no
frame capture, no graphics pipeline. The reasoning about statistics and budgets
transfers; the engineering does not, and `context` tier is the honest claim.

## How to prove it

**The artifact.** A deadline sweep over a workload of yours, reported as a miss
rate and a tail rather than an average.

**Three things to do, in order:**

1. Run the sweep in step 2. Predict the period at which misses begin, then look
   at what the median does on either side of it.
2. Take any latency claim in your own documentation and work out whether it
   could be true while the system fails a third of the time. If the claim is a
   mean or a median, it can.
3. Add the scheduling or framework overhead to one published cost figure. On an
   idle machine it was a third again here, and readers budget with the number
   you give them.

**What makes it credible rather than decorative.** The sweep ran on this
machine and the script is a dozen lines, so the flat median against a 30 per
cent miss rate and the cliff between 2.0 and 1.5 ms are both reproducible.
What is absent is the domain's actual engineering: no real-time kernel, no
graphics pipeline, no frame profiler, no hardware timing. The
[demonstrated](../demonstrated.md) page records this as the statistics rather
than the systems work.

## Related

- [Inference serving and microservices](inference-serving.md), the same tail problem without a deadline
- [GPU computing and CUDA](gpu-computing.md), where frame work actually runs
- [Robotics simulation, Isaac Sim and ROS](robotics-sim.md), deadlines plus physics
- [Cognitive load in technical content](cognitive-load.md), where the per-item against aggregate lesson recurs
