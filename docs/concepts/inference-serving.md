---
title: Inference serving and microservices
summary: "Batching bought 14x throughput and cost 21x latency, and past a knee at batch 16 it bought nothing and still cost."
diataxis: explanation
audience: developer
concept: inference-serving
tags: [dom, context]
---

# Inference serving and microservices

`context` · difficulty 2 · 4h

!!! quote "Asked for by name"
    Intel: "including inference microservices and the agentic toolkit"

**Leads to:** [Reading an AI software stack](ai-stack.md)

## What it is

Putting a trained model behind a network interface so other services can use
it. The model is fixed; everything interesting is the serving layer: batching,
queueing, concurrency, warm-up, and which number you promise.

Intel's phrase is "inference microservices", which is the current packaging:
the model, a runtime, a server and a health check shipped as a container with
an endpoint. The documentation obligations follow from that being an operable
service rather than a library.

## Why the job asks for it

Because the thing a reader has to get right is a tradeoff, and tradeoffs are
where documentation either earns its keep or misleads at scale.

An inference service has two performance numbers that move in opposite
directions. Vendors publish the flattering one. A reader who deploys against
the published figure and then watches their p99 is the single most common
support path in this area, and the fix is almost always a configuration
decision that a page could have explained.

## The golden path

Measure latency against throughput on a real runtime, and find the point where
the tradeoff stops being a tradeoff. About thirty minutes, CPU only, no model
download.

**Step 1: a real model on a real runtime**

ONNX Runtime, with two matmuls big enough that compute dominates:

```python
g = helper.make_graph(
    [helper.make_node("MatMul", ["x", "w1"], ["h"]),
     helper.make_node("Relu", ["h"], ["hr"]),
     helper.make_node("MatMul", ["hr", "w2"], ["y"])], "mlp", ...)
sess = ort.InferenceSession("big.onnx", providers=["CPUExecutionProvider"])
```

```
model: 33.6 MB of weights, two 1024x4096 matmuls
```

**Step 2: sweep the batch size and report both numbers**

The column that matters is the last one. Requests arriving at 500 per second
have to wait for a batch to fill before it runs, so the latency a request
experiences is that wait plus the compute:

```
  batch  batch ms   per-req ms   throughput   wait for a full batch   total latency
                    (compute)      req/s      at 500 req/s             p50 ms
      1      1.51       1.51          662                0.0             1.5
      2      1.43       0.72         1398                2.0             3.4
      4      1.45       0.36         2765                6.0             7.4
      8      1.55       0.19         5164               14.0            15.5
     16      1.69       0.11         9448               30.0            31.7
     32      3.42       0.11         9370               62.0            65.4
     64      6.78       0.11         9439              126.0           132.8
```

Three things are in that table and only one of them usually gets published.

**Throughput rises 14x**, from 662 to 9,448 requests per second. That is the
number in the benchmark.

**Per-request compute falls 14x**, from 1.51 ms to 0.11 ms. That is the number
in the datasheet, and it is true: once a batch is running, each request's share
of the work really is 0.11 ms.

**The latency a request experiences rises 21x**, from 1.5 ms to 31.7 ms,
because it spent 30 ms waiting for nineteen strangers to arrive. No request
anywhere in the system ever experienced 0.11 ms.

**Step 3: find the knee**

Past batch 16, throughput stops moving: 9,448, then 9,370, then 9,439. Within
noise, identical. Latency keeps climbing: 31.7 ms, 65.4, 132.8.

```
batch 16 -> 64:   throughput  +0%        latency  +4x
```

So there is a configuration that is simply wrong rather than a tradeoff. The
machine saturated at 16, and every batch size above it pays latency for
nothing. A reader cannot deduce where that knee is, because it depends on the
model, the hardware and the arrival rate, which is exactly why the
documentation's job is to tell them to measure it rather than to publish a
default.

**Step 4: the number to promise**

Given the table, the honest commitment is a pair with an arrival rate attached:

```
at 500 req/s, batch 16:  ~9,400 req/s capacity, p50 latency 31.7 ms
at 500 req/s, batch 1:   ~660 req/s capacity,  p50 latency 1.5 ms
```

Either row is defensible. "0.11 ms per request" is not, although it is
arithmetically true, which is what makes it the most effective misleading
number in this field.

**What you built.** A measured latency-throughput curve on a real runtime, a
saturation knee past which batching is pure loss, and three defensible ways to
state the result instead of one flattering one.

## Reference

### The numbers, and what each one hides

| Number | True when | Hides |
|---|---|---|
| Throughput, req/s | Under sustained load | What any one request waited |
| Per-request compute | Inside a running batch | The queue |
| p50 latency | Half the time | The tail that pages someone |
| p99 latency | The number users feel | Cost, since it drives headroom |
| Time to first token | Streaming models | Total completion time |
| Cold-start latency | The first request after a scale-up | Everything, on bursty traffic |

A service characterised by one of these is characterised by none of them. The
pair worth documenting is a latency percentile at a stated arrival rate.

### Batching strategies

| Strategy | Latency | Throughput | Use |
|---|---|---|---|
| None, one request per call | Best | Worst | Interactive, low volume |
| Fixed batch, wait to fill | Worst | Best | Offline and bulk |
| Dynamic batch with a timeout | Bounded | Most of the gain | The usual right answer |
| Continuous or in-flight batching | Good | Best, for generative | Token-by-token models |

The timeout in row three is the parameter that makes the tradeoff tunable, and
it is the one most often left at a default nobody measured.

### What an inference microservice has to document

| Item | Why |
|---|---|
| The latency-throughput curve, with arrival rate | Otherwise the reader picks a batch size blind |
| The saturation point | Above it, configuration is loss, not tradeoff |
| Cold-start time | Determines whether autoscaling can work |
| Warm-up requirement | First-call latency is often 10x |
| Input shape and dtype contract | The commonest integration failure |
| Health against readiness | A loaded model is not a ready one |
| Memory per replica, at the chosen batch | Capacity planning needs it |
| Version of model, runtime and server | Three numbers, see the [stack](ai-stack.md) |

Rows six and seven are the ones that turn a demo into something operable, and
they are the ones a research-led team is least likely to write.

### Health against readiness

| Probe | Should mean |
|---|---|
| Liveness | The process is not wedged |
| Readiness | The model is loaded and warm |

Conflating them produces a service that receives traffic before its weights are
in memory, so the first requests after every deploy are the slowest, and the
dashboard blames the network.

### Where latency actually goes

| Stage | Typically |
|---|---|
| Network and serialisation | Small, until payloads are images |
| Queue wait | Dominant under batching; see step 2 |
| Preprocessing | Often on the critical path, often forgotten |
| Model compute | The only part benchmarks measure |
| Postprocessing | Same as preprocessing |
| Cold start | Enormous, and excluded from averages |

Preprocessing is the one to raise in a review. It runs per request, is usually
single-threaded Python, and is absent from every published figure.

## How to talk about it

**Lead with the two numbers moving in opposite directions.** "An inference
service has a throughput number and a latency number and batching trades one
for the other. I measured it on ONNX Runtime: going from batch 1 to 16 bought
14x throughput, 662 to 9,400 requests a second, and cost 21x latency, 1.5 ms to
31.7, because at 500 arrivals a second a request waits 30 ms for nineteen
strangers before any compute happens."

**Then the number that is true and misleading.** Per-request compute falls from
1.51 ms to 0.11 ms, and that is arithmetically correct: inside a running batch
each request's share really is 0.11 ms. No request in the system ever
experienced it. That is the figure that ends up on a datasheet, and the support
path it creates is a reader deploying against it and then looking at their p99.

**The finding I would actually bring to a planning meeting.** Past batch 16 the
throughput stopped moving, 9,448 then 9,370 then 9,439, while latency went to
65 and then 133 ms. Above the knee it is not a tradeoff, it is a wrong setting.
And a reader cannot work out where the knee is, since it depends on model,
hardware and arrival rate, so the documentation's job is to tell them to
measure it rather than to ship a default that looks authoritative.

**Be honest about the depth.** This is a CPU runtime, one model shape, no GPU,
no real server, no autoscaler and no production traffic. It is enough to reason
correctly about the tradeoff and to know which questions to ask, and it is not
operational experience of running inference at scale. For a documentation role
I would rather state that boundary than imply the other thing.

## How to prove it

**The artifact.** A latency-throughput sweep on whatever runtime you have, with
queue wait included and the knee identified.

**Three things to do, in order:**

1. Run the sweep in step 2 on any model you have. Include the queue wait
   column; it is the one that changes the decision and the one no benchmark
   prints.
2. Find a published per-request latency for a service you use and work out
   whether it is compute-only. If the batch size is not stated next to it, it
   is.
3. Time the first request after a restart against the hundredth. The ratio
   decides whether autoscaling is viable, and it is rarely documented.

**What makes it credible rather than decorative.** The measurements ran against
ONNX Runtime 1.29 with a 33.6 MB two-matmul model on this machine's CPU, and
the sweep is a short script. What is absent is everything operational: no GPU,
no Triton or comparable server, no containers, no autoscaling, no real traffic
and no tail-latency work under contention. The [demonstrated](../demonstrated.md)
page records this as partial on that basis, and `context` tier is the honest
claim.

## Related

- [Reading an AI software stack](ai-stack.md), the versions underneath this
- [GPU computing and CUDA](gpu-computing.md), where the compute usually runs
- [Real-time and graphics systems](realtime-systems.md), the same tail-latency problem with a deadline
- [Time to first success](time-to-first-success.md), the documentation metric with the same shape
