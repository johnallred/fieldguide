---
title: GPU computing and CUDA
summary: "No GPU was available, so this page measures arithmetic intensity on a CPU and verifies the compatibility rules by reading them: the promise is one line and its exceptions are five."
diataxis: explanation
audience: developer
concept: gpu-computing
tags: [dom, context]
---

# GPU computing and CUDA

`context` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Documentation experience in graphics, simulation, robotics, or real-time systems"

!!! warning "No GPU was available"
    This machine has no NVIDIA device, so nothing on this page was run on a GPU. The measurement in step 1 is a CPU analogue of a GPU lesson and is labelled as such; the compatibility material in step 3 was verified by opening NVIDIA's own documentation. Where this page reasons rather than demonstrates, it says so.

## What it is

Running computation on a processor with thousands of simple cores instead of a
few complex ones. The programming model is a grid of threads executing the same
instruction over different data, which suits dense regular arithmetic and
suits nothing else.

For a documentation role the useful framing is not the hardware. It is that GPU
performance is governed by **data movement rather than arithmetic**, and that
the toolchain's compatibility rules are the largest source of reader pain.

## Why the job asks for it

NVIDIA lists graphics, simulation, robotics and real-time systems, and CUDA is
underneath all four. The role writes for people whose code already works and is
slower than they expected, or does not build at all.

Both of those have documentable causes, and neither is about kernel
programming. The first is arithmetic intensity, which is arithmetic a reader
can do before porting anything. The second is a version matrix.

## The golden path

Measure why moving work to a faster processor often changes nothing. About
twenty minutes.

**Step 1: arithmetic intensity, measured on the processor that is here**

Four operations on 2048×2048 float32 arrays, timed with their bytes moved and
their floating-point operations counted:

```python
ops = [("copy  A -> C", lambda: np.copyto(C, A),        2*N*N*4,  0),
       ("add   A + B",  lambda: np.add(A, B, out=C),    3*N*N*4,  N*N),
       ("2A + B",       lambda: np.add(2*A, B, out=C),  4*N*N*4,  2*N*N),
       ("matmul A @ B", lambda: np.matmul(A, B, out=C), 3*N*N*4,  2*N**3)]
```

```
operation                     ms       GB/s      GFLOP/s flops/byte
copy        A -> C          2.06       16.3          0.0       0.00
add         A + B           4.64       10.9          0.9       0.08
scale+add   2A + B          7.48        9.0          1.1       0.12
matmul      A @ B         139.40        0.4        123.2     341.33
```

The three elementwise operations all land near 9 to 16 GB/s and achieve about
one GFLOP/s. The matmul achieves **123 GFLOP/s, over a hundred times more
compute**, on the same arrays, on the same chip, in the same library.

The reason is the last column. Matmul reuses each byte it loads 341 times;
`add` uses each byte once and a bit. The elementwise operations are not
compute-limited at all, they are waiting for memory, and a processor with more
arithmetic units would not help them.

**That is the GPU lesson, and it is why this CPU measurement is worth
publishing.** A kernel at 0.08 flops per byte moved to a device with ten times
the compute and three times the bandwidth gets roughly three times faster, not
ten, and then the transfer across PCIe is subtracted from even that. The
question "will the GPU help" is answerable with a division before anybody
writes a kernel.

The honest limits of the analogue: a GPU's bandwidth, its memory hierarchy,
coalescing rules, occupancy and warp divergence are all absent here. The ratio
argument transfers; none of the numbers do.

**Step 2: the arithmetic a page should hand the reader**

```
arithmetic intensity = flops performed / bytes moved
if  intensity  <  device_flops / device_bandwidth   ->  memory bound
```

A page that states the device's ratio and shows the reader how to compute
theirs has answered the most common pre-port question in this domain. Most
documentation instead explains how to launch a kernel.

**Step 3: the compatibility rules, verified by reading them**

The second thing readers arrive with is a build or load failure, and the rules
are genuinely intricate. From NVIDIA's own compatibility documentation, opened
and read rather than recalled:

Minor version compatibility means an application built with a toolkit in a
major release family runs on any driver meeting a minimum version, 580 or newer
for CUDA 13.x, 525 for 12.x, 450 for 11.x. The page then states five
qualifications:

```
1  feature set is limited; newer-driver features fail with
   cudaErrorCallRequiresNewerDriver
2  code compiled to PTX does not work on older drivers
3  a target architecture must be passed to nvcc, such as -arch=sm_xx
4  without the minimum driver installed, calls return an initialisation error
5  libraries have interdependencies: each cuDNN version requires a
   particular cuBLAS
```

**The promise is one sentence and its exceptions are five.** The structural
observation is the transferable one: any summary of this short enough for a
reader to remember is wrong, so a compatibility page cannot be simplified into
a sentence, and the instinct to try is the thing to resist. What works instead
is a table with the carve-outs as rows and a symptom column, because readers
arrive with a symptom.

*(Verified by opening
[NVIDIA's minor version compatibility page](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html).
The driver versions, the error constant and all five carve-outs are quoted from
that page. I have not run CUDA on any machine in this project.)*

**What you built.** A measured demonstration that performance follows data
movement rather than arithmetic, the division a reader should do before porting
anything, and a verified account of why the compatibility story cannot be
compressed.

## Reference

### The model, in the terms readers will meet

| Term | Means | Why documentation mentions it |
|---|---|---|
| Kernel | A function run by many threads | The unit of GPU work |
| Thread, block, grid | The launch hierarchy | Launch configuration questions |
| Warp | 32 threads executing together | Divergence costs |
| Occupancy | Active warps against the maximum | The usual tuning knob |
| Coalescing | Neighbouring threads reading neighbouring memory | The usual performance bug |
| Shared memory | Fast memory local to a block | The usual optimisation |
| Host and device | CPU and GPU, with separate memory | The usual correctness bug |
| Stream | A queue of asynchronous work | Overlapping transfer and compute |
| Compute capability | A device's feature level, such as `sm_90` | Build flags and support matrices |

### Why ported code is often not faster

| Cause | Check |
|---|---|
| The kernel is memory bound | Arithmetic intensity, step 1 |
| Transfers dominate | Time the copy separately from the kernel |
| The work is too small | Launch overhead exceeds the work |
| Uncoalesced access | A profiler, or the access pattern |
| Warp divergence | Branches depending on thread index |
| Synchronisation each step | Measure with the synchronise removed |
| Timing without synchronising | The launch is asynchronous; the timer lies |

The last row produces reports of impossibly fast kernels and belongs in any
getting-started page, because a reader who measures wrongly will optimise
wrongly for a week.

### The version matrix a reader needs

| Axis | Example | Symptom when wrong |
|---|---|---|
| Driver version | 580, 525, 450 | Initialisation error |
| Toolkit version | CUDA 13.1 | Build failure |
| Compute capability | `sm_90` | No kernel image for device |
| PTX against cubin | `-arch` flags | Fails on older drivers |
| Library pairings | cuDNN with cuBLAS | Load-time symbol errors |
| Framework build | A wheel pinned to a CUDA minor | Silent CPU fallback |

The last row is the quiet one: a framework that cannot see the GPU often falls
back to CPU and reports success, so the reader's job runs correctly and
twenty times slower with no error anywhere.

### What a GPU page should contain, and usually does not

| Should | Usually has |
|---|---|
| The arithmetic for "will this help" | How to launch a kernel |
| A support matrix with symptoms | A prose paragraph on compatibility |
| How to time correctly, with synchronisation | Timings with no caveat |
| The transfer cost, separately | Kernel time only |
| A detection snippet for silent CPU fallback | An assumption it worked |
| The minimum driver, stated numerically | "A recent driver" |

## How to talk about it

**Lead with the honest boundary, because it is better than bluffing.** "I have
not shipped CUDA. What I can do is the reasoning a documentation role needs:
GPU performance follows data movement rather than arithmetic, and the
compatibility rules are the main source of reader pain. I measured the first
part on a CPU, which is where the lesson is visible without a device."

**Then the measurement.** On the same arrays with the same library, elementwise
operations hit about one GFLOP/s and a matmul hit 123, a hundredfold
difference, because matmul reuses each loaded byte 341 times and `add` uses it
once. So the elementwise work is not compute-limited, it is waiting for memory,
and moving it to a device with more arithmetic units does nearly nothing. "Will
the GPU help" is a division a reader can do before porting anything, and most
documentation teaches kernel launches instead.

**The compatibility point, with the source named.** NVIDIA's minor version
compatibility page promises that applications in a major family run on any
driver above a minimum, 580 for 13.x, 525 for 12.x, 450 for 11.x, and then
carves out five exceptions: feature set, PTX, the `-arch` requirement, the
minimum driver actually being present, and library interdependencies. One line
of promise, five of exceptions. No summary short enough to remember is correct,
so the page has to be a table keyed by symptom, since symptoms are what readers
arrive with.

**The thing I would add to any getting-started page.** Kernel launches are
asynchronous, so a reader who times without synchronising measures the launch
rather than the work and reports an impossibly fast kernel. And a framework
that cannot see the device often falls back to CPU and reports success, so the
job runs correctly and twenty times slower with nothing in the logs. Both are
cheap to document and both cost readers days.

**What I would not claim.** No kernel I have written, no profiler I have run,
no occupancy I have tuned. For a documentation role at `context` depth that is
the right boundary, and I would want an engineer's review on anything past the
arithmetic.

## How to prove it

**The artifact.** An arithmetic-intensity table for the operations your readers
actually run, and a symptom-keyed compatibility matrix.

**Three things to do, in order:**

1. Run step 1 on any machine. Predict the ratio between the elementwise GFLOP/s
   and the matmul's before you look; a hundredfold gap surprises most people.
2. Compute arithmetic intensity for one kernel your team is thinking of
   porting, and compare it with the device's flops-per-byte. That division has
   cancelled porting projects.
3. Find a timing claim in GPU documentation you rely on and check whether it
   synchronised. If the page does not say, assume it did not.

**What makes it credible rather than decorative.** The intensity measurement ran
here on CPU with numpy and is reproducible, and the compatibility figures were
verified by opening NVIDIA's documentation, which is cited as reading. No GPU,
no CUDA, no kernel, no profiler: the [demonstrated](../demonstrated.md) page
records this concept as having no demonstration in either repository, which is
the accurate statement, and `context` tier is the claim being made.

## Related

- [Reading an AI software stack](ai-stack.md), the layers above the driver
- [Inference serving and microservices](inference-serving.md), the usual workload
- [Real-time and graphics systems](realtime-systems.md), where frame budgets come from
- [Reproducible environments](reproducible-environments.md), how a version matrix gets pinned

## Sources

- [Minor Version Compatibility, NVIDIA CUDA Compatibility documentation](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html), opened and read for the driver versions, the `cudaErrorCallRequiresNewerDriver` constant and all five carve-outs.
