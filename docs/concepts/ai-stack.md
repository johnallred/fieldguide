---
title: Reading an AI software stack
summary: "The newest onnx writes a file the newest onnxruntime refuses to load, and the error message is a C++ function signature and a path on somebody else's build machine."
diataxis: explanation
audience: developer
concept: ai-stack
tags: [dom, context]
---

# Reading an AI software stack

`context` · difficulty 2 · 4h

!!! quote "Asked for by name"
    Intel: "Python literacy sufficient to run and validate AI samples, with working familiarity with the AI software stack"

**Prerequisites:** [Inference serving and microservices](inference-serving.md)

## What it is

The layered set of components between a model and the silicon: a framework, an
exchange format, a runtime, a kernel library, a driver. Intel's bullet asks for
"Python literacy sufficient to run and validate AI samples", which is a precise
and modest requirement: not building models, but being able to run a sample and
tell whether its output is right.

The reason it needs a page is that the layers have independent version numbers
and the compatibility rules between them are the single largest source of
support load in this field.

## Why the job asks for it

Because "run and validate AI samples" is the job description of a person who
will spend their first month on version errors.

A documentation engineer in this space does not debug kernels. They do
repeatedly answer the question "why does the sample not load", and the answer is
nearly always a pair of version numbers that are each individually current and
jointly unsupported. Writing that down, once, correctly, is worth more than any
tutorial.

## The golden path

Install the newest versions of two adjacent components and try to pass a file
between them. About twenty minutes, and the first result is the whole page.

**Step 1: what is installed**

```python
import onnx, onnxruntime as ort
print(onnx.__version__, onnx.IR_VERSION, onnx.defs.onnx_opset_version())
print(ort.__version__)
```

```
onnx          1.23.2   (writes IR 14, knows opset 28)
onnxruntime   1.29.0
```

Both current, both installed today, nothing pinned.

**Step 2: write a two-line model and load it**

A single `Relu`. There is no simpler model.

```python
m = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
onnx.save(m, "d.onnx")
ort.InferenceSession("d.onnx")
```

```
onnx 1.23.2 make_model default ir_version = 14
  onnxruntime 1.29.0 refuses it:
  [ONNXRuntimeError] : 1 : FAIL : Load model from d.onnx failed:
  /onnxruntime_src/onnxruntime/core/graph/model.cc:192
  onnxruntime::Model::Model(onnx::ModelProto&&, const onnxruntime::PathString&,
  const onnxruntime::IOnnxRuntimeOpSchemaRegistryList*,
  const onnxruntime::logging::Logger&, const onnxruntime::ModelOptions&) Un
```

**The default output of the newest writer is not loadable by the newest
reader.** No flags, no exotic operators, a single `Relu`, and the two most
obvious packages in the ecosystem disagree out of the box.

The message deserves its own look. A reader is handed a path on NVIDIA's build
machine, a fully-qualified C++ constructor signature, and then the text is
truncated before it says what to do. The fix is one line, `m.ir_version = 10`,
and it is not in the message.

**Step 3: the version matrix has more than one axis**

Opset and IR version are different numbers that fail differently:

```
model as written           what onnxruntime does with it
opset 17, IR 10            loads and runs
opset 28, IR 10            FAIL ... ValidateOpsetForDomain ... (load-time)
opset 17, IR 14            FAIL ... Model::Model ... (load-time)
opset 1,  IR 10            loads, warns twice, then:
                           NOT_IMPLEMENTED : Could not find an implementation
                           for Relu(1) node with name ''
```

Four outcomes from one `Relu`. Two axes, two directions, and the fourth row is
the interesting one: an opset that is too **old** passes validation, emits a
warning saying it "may run depending upon legacy support", and then fails at a
different layer with a different error class when the node is bound.

So the same category of problem, a version mismatch, surfaces as a load error
in one direction and a runtime error in the other, which means a troubleshooting
page organised by error message will put them in different sections.

**Step 4: write the table nobody wrote**

Everything above fits in six lines, and would have saved the reader the
afternoon:

```
component     version    writes / accepts
onnx          1.23.2     writes IR 14 by default; set ir_version yourself
onnxruntime   1.29.0     accepts IR <= 10, opset 7..23 (guaranteed >= 7)
fix           m.ir_version = 10
symptom       FAIL at InferenceSession(), message names a .cc file
```

That is the artifact. Not a tutorial, not a conceptual explanation of ONNX: a
table of which versions accept which, the one-line fix, and the symptom text a
reader will paste into a search box.

**What you built.** A reproduced incompatibility between two current packages, a
mapped two-axis version matrix, and the compatibility table that the error
message replaces.

## Reference

### The layers, from model to metal

| Layer | Examples | Breaks as |
|---|---|---|
| Framework | PyTorch, TensorFlow, JAX | Training-time API churn |
| Exchange format | ONNX | Opset and IR version |
| Runtime | ONNX Runtime, OpenVINO, TensorRT | Unsupported operator |
| Kernel library | cuDNN, oneDNN, cuBLAS | Version pinned to the runtime |
| Driver and toolkit | CUDA, ROCm, Level Zero | Minimum driver version |
| Hardware | GPU, CPU, accelerator | Compute capability |

A single sample exercises every row, and an error from any row arrives at the
reader as "the sample does not work".

### Why the errors are bad, specifically

| Property of the message | Consequence |
|---|---|
| Names a source file on a build machine | Looks like an internal defect |
| Includes a C++ signature | Unsearchable, unreadable |
| Truncated before the remedy | The fix is one line and absent |
| Error class differs by direction | Troubleshooting pages split the cause |
| Warnings that say "may work" | Readers proceed and fail later |

These are the most-read strings in the stack, since a stuck reader is a
motivated reader, and they are maintained by nobody. A documentation role that
gets the fix into the message has done more good than a dozen pages.

### What to pin, and where

| Practice | Why |
|---|---|
| Pin every layer in the sample's requirements | A floating version breaks the sample on a schedule |
| State the tested combination in the page | The reader's combination will differ |
| Run the sample in CI on the pinned set | Otherwise the page's claim rots silently |
| Test the newest set too, and let it fail loudly | So you learn before the reader does |
| Record the fix next to the symptom text | Readers search symptoms, not causes |

Row four is the one teams skip. A sample pinned forever works forever and tells
you nothing about the ecosystem your readers actually install into.

### Validating a sample's output, not just its exit code

| Check | Catches |
|---|---|
| Exit code | Crashes only |
| Output shape and dtype | Most integration errors |
| Output against a stored reference | Numerical drift between versions |
| Tolerance stated explicitly | False failures on different hardware |
| A known-wrong input | A sample that cannot fail |

Intel's phrase is "run **and validate**", and the distance between rows one and
three is the whole of it. A sample asserted only on exit code passes while
producing nonsense, which is the characteristic AI-sample defect.

### CUDA minor version compatibility, as an example of a promise with carve-outs

NVIDIA's compatibility documentation states that from CUDA 11 onward,
applications built with a toolkit in a major release family run on any driver
meeting a minimum version, 580 or newer for 13.x, 525 for 12.x, 450 for 11.x.
The same page then carves out five exceptions:

- The feature set is limited, and newer-driver features fail with
  `cudaErrorCallRequiresNewerDriver`.
- Code compiled to PTX does not work on older drivers.
- A target architecture must be passed to `nvcc`.
- The minimum driver must actually be installed, or calls return an
  initialisation error.
- Libraries have interdependencies of their own: each cuDNN version requires a
  particular cuBLAS.

The useful observation is structural rather than about CUDA: **the promise fits
in one line and its exceptions take five**, so any summary short enough to
remember is wrong. That is worth knowing before writing a compatibility page,
because the instinct is to simplify exactly the thing that cannot be
simplified.

*(Verified by opening
[NVIDIA's minor version compatibility page](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html);
the figures and carve-outs above are from that page, not from search results.)*

## How to talk about it

**Lead with the version problem, because it is the job.** "Running and
validating AI samples sounds modest, and in practice it means becoming the
person who answers 'why does the sample not load'. The answer is nearly always
two version numbers that are each individually current and jointly
unsupported."

**Then the demonstration, which is short enough to say out loud.** I installed
the newest `onnx` and the newest `onnxruntime`, wrote a model containing a
single `Relu`, and `onnxruntime` refused to load it, because `onnx` now writes
IR version 14 by default and the runtime accepts 10. No flags, no unusual
operators, the two most obvious packages in the ecosystem, incompatible out of
the box. The fix is one line.

**The part a documentation person should care about.** The error message hands
the reader a path on somebody's build machine, a fully-qualified C++
constructor signature, and no remedy. Those strings are the most-read
documentation in the stack, because a stuck reader is a motivated reader, and
nobody owns them. I would rather land the fix inside the message than write
another page.

**The structural point, with a worked example.** NVIDIA's CUDA minor-version
compatibility page promises that apps in a major family run on any driver above
a minimum, and then carves out five exceptions: PTX, feature set, the `-arch`
requirement, the minimum driver actually being installed, and library
interdependencies. The promise is one line and the exceptions are five, so
every summary short enough to remember is wrong. Knowing that before writing a
compatibility page changes what you write, because the instinct is to simplify
precisely what cannot be.

**Be honest about the depth.** CPU only, no GPU, no CUDA, no TensorRT, no
OpenVINO, no distributed training. I can run a sample, read a version matrix,
and tell whether output is plausible. I would not claim to debug a kernel or
tune an accelerator, and `context` tier is what this is.

## How to prove it

**The artifact.** A compatibility table for two components you use, with the
symptom text, the accepted ranges and the one-line fix.

**Three things to do, in order:**

1. Install the newest versions of two adjacent components in a stack you care
   about and pass the simplest possible artifact between them. Predict whether
   it works; this page exists because the answer was no.
2. Take the next version error you hit and write the three-line entry that
   would have saved you: symptom, cause, fix. That is the page the ecosystem is
   missing.
3. Check whether a sample you own asserts anything about its output beyond the
   exit code. "Run and validate" is two verbs and most samples do one.

**What makes it credible rather than decorative.** Every result was executed
here against `onnx` 1.23.2 and `onnxruntime` 1.29.0, including the full error
text and the four-outcome version matrix. The CUDA material is verified by
opening NVIDIA's own compatibility page, and is cited as reading rather than as
experience: no CUDA, no GPU and no driver work happened on this machine. The
[demonstrated](../demonstrated.md) page records the ONNX half as demonstrated
and the accelerator half as not.

## Related

- [Inference serving and microservices](inference-serving.md), what runs on this stack
- [GPU computing and CUDA](gpu-computing.md), the layer underneath
- [Reproducible environments](reproducible-environments.md), how to pin all of it
- [Code-sample validation](code-sample-validation.md), the "and validate" half
