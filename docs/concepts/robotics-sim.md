---
title: Robotics simulation, Isaac Sim and ROS
summary: "Two frames, both required, that disagree on purpose: one drifts without bound and never jumps, the other stays accurate and jumps, and differentiating the wrong one invents 1.2 m/s of velocity."
diataxis: explanation
audience: developer
concept: robotics-sim
tags: [dom, context]
---

# Robotics simulation, Isaac Sim and ROS

`context` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Documentation experience in graphics, simulation, robotics, or real-time systems; familiarity with USD, Omniverse, Isaac Sim, or ROS"

!!! warning "No simulator was run"
    No ROS, no Isaac Sim and no robot were available here. The measurement in step 2 is a simulation of the frame properties that ROS specifies, written to demonstrate why the specification says what it does; the specification itself in step 1 was verified by opening it. Nothing on this page is experience of operating a robot.

**Prerequisites:** [OpenUSD and Omniverse](usd-omniverse.md)

## What it is

Running a robot's software against a simulated body and world instead of
hardware. Isaac Sim is NVIDIA's simulator, built on Omniverse and therefore on
[USD](usd-omniverse.md); ROS is the middleware most robot software is written
against, and the two meet through a bridge.

For a documentation role the domain's defining difficulty is not physics. It is
that a robot's software maintains **several descriptions of where it is**, those
descriptions disagree, and the disagreement is deliberate.

## Why the job asks for it

Because the concept that costs readers the most is a choice between two things
that both look correct.

NVIDIA groups robotics with graphics, simulation and real-time systems, and
documentation in all four has to explain a model before it can explain an API.
In robotics, the model is the transform tree, and the specific thing that bites
is which frame to read a position from. Getting it wrong produces software that
works in a demo and misbehaves on a robot, which is the most expensive class of
documentation failure in this domain because the feedback arrives late and
looks like a hardware fault.

## The golden path

Read what ROS actually specifies about coordinate frames, then demonstrate why
it specifies it. About twenty-five minutes.

**Step 1: the specification, opened and read**

ROS standardises this in REP 105, which names four frames and a strict
single-parent tree:

```
earth  ->  map  ->  odom  ->  base_link
```

Each frame has exactly one parent, so attaching `base_link` to both `map` and
`odom` is forbidden. The two interesting frames carry opposite guarantees:

```
odom   the pose of a robot in the odom frame is guaranteed to be continuous,
       and can drift over time, without any bounds

map    the map frame is not continuous; its pose can change in discrete
       jumps at any time
```

And each transform has an owner: an odometry source publishes
`odom` → `base_link`; the localisation component publishes `map` → `odom`,
deliberately **not** `map` → `base_link`, by taking the odometry transform and
correcting it; `earth` → `map` is static.

*(Verified by opening
[REP 105](https://reps.openrobotics.org/rep-0105/). The frame names, the tree
ordering, the continuity language and the ownership of each transform are from
that document.)*

Two frames, both required, with contradictory properties. That is the model a
page has to land before any API appears.

**Step 2: why those properties are the way round**

Simulate twenty metres of travel with two per cent wheel slip and a
localisation fix every twenty-five steps:

```python
odom += V * DT * (1 + rng.normal(0, 0.02))       # integrates slip, smoothly
if fix_arrives:
    map_est = truth + rng.normal(0, 0.03)        # snaps to the fix
else:
    map_est += V * DT * (1 + rng.normal(0, 0.02))
```

```
                                 odom frame    map frame
error at the end                   -0.045 m     -0.024 m
worst error                         0.050 m      0.070 m
largest single-step change         0.0065 m     0.1203 m
```

The last row is the whole point. The `odom` frame's error never changes by more
than 6.5 mm in a step; the `map` frame's jumps by 120 mm the instant a fix
lands.

Now consider a controller that estimates velocity by differentiating position,
which is an ordinary thing to do:

```
a controller differentiating the map frame sees 1.2 m/s of phantom velocity
```

On a robot travelling at 1.0 m/s, reading the globally-accurate frame produces
a **120 per cent velocity error** at every localisation update, out of nowhere,
with every component behaving correctly. Read `odom` instead and the velocity is
smooth and the position slowly wrong, which for a controller is the right
trade.

So the rule a page should state plainly: **differentiate `odom`, navigate in
`map`, and never mix them in one calculation.** The specification implies it;
saying it outright is the documentation contribution.

**Step 3: what this says about writing for the domain**

The transform tree is a prerequisite, not a reference topic. A reader who has
not understood that two frames disagree on purpose cannot use any of the API
correctly, and will write code that passes in simulation, where slip can be
zero and fixes can be perfect.

That is the sim-to-real gap in its documentable form: a simulator can be
configured so that the distinction this page is about does not appear, which
means a tutorial that only runs in simulation can teach the wrong model
without ever failing.

**What you built.** A verified reading of the frame specification, a
demonstration of why its two guarantees are opposite, and a one-line rule with
a measured consequence behind it.

## Reference

### The frames, and who owns each transform

| Transform | Published by | Continuous | Drifts |
|---|---|---|---|
| `earth` → `map` | Static, or localisation | n/a | No |
| `map` → `odom` | Localisation | No, jumps | No |
| `odom` → `base_link` | Odometry source | Yes | Yes, unbounded |

Reading a pose in `map` composes a jumping transform with a smooth one, which
is why the result jumps. Reading in `odom` omits the correction, which is why
it drifts.

### Choosing a frame

| For | Use | Because |
|---|---|---|
| Velocity, by differentiation | `odom` | Continuity; see step 2 |
| Local obstacle avoidance | `odom` | Short horizon, needs smoothness |
| Navigation to a goal | `map` | Global accuracy |
| Logging a trajectory | Both, labelled | They answer different questions |
| Anything spanning a localisation update | `odom`, then transform once | Mixing invents motion |

### Terms worth recognising

| Term | Means |
|---|---|
| TF, tf2 | The transform library and its tree |
| Odometry | Pose estimated by integrating motion |
| SLAM | Building a map while localising in it |
| URDF, SDF | Robot description formats; USD in Isaac Sim |
| Joint state | Positions and velocities of the articulated parts |
| Twist | A linear and angular velocity command |
| Node, topic, service, action | The ROS communication primitives |
| Sim-to-real gap | Behaviour that holds in simulation and not on hardware |
| Domain randomisation | Varying simulation parameters to close that gap |

### Where the sim-to-real gap comes from

| Source | How a simulator usually differs |
|---|---|
| Sensor noise | Absent or Gaussian, rather than structured |
| Contact and friction | Approximated; the hardest part of physics |
| Latency | Zero, or constant, rather than variable |
| Timing | Simulation time, which can pause |
| Actuator dynamics | Instantaneous, rather than ramped |
| Localisation quality | Can be made perfect, hiding the step 2 problem |

The bottom row is the one that interacts with documentation: a tutorial written
and tested entirely in simulation can be correct, reproducible, CI-verified and
still teach a model that fails on a robot.

### Simulation time against wall-clock time

A simulator can run faster or slower than real time and can be stepped or
paused. Code that reads the system clock instead of the simulation clock
behaves differently under simulation, and this is a documentation obligation
rather than a footnote: any sample that times anything has to say which clock
it uses.

### What a page in this domain owes the reader

| Owes | Rather than |
|---|---|
| The frame model, before any API | A tf2 API reference |
| Which frame to use for which question | "Use tf2 to transform" |
| An explicit statement that frames disagree | Leaving it implied |
| Which clock a sample reads | Assuming wall-clock |
| What the simulator does not model | Implying parity with hardware |
| A hardware-verified claim marked as such | Mixing simulated and real results |

## How to talk about it

**Lead with the boundary and then the model.** "I have not operated a robot.
What I can do is the documentation reasoning, and in robotics that starts with
the transform tree, because a robot maintains several descriptions of where it
is and they disagree on purpose."

**Then the specification, precisely.** ROS's REP 105 defines a single-parent
tree, `earth` to `map` to `odom` to `base_link`, and gives two of those frames
opposite guarantees: `odom` is guaranteed continuous and drifts without bound,
`map` is explicitly not continuous and can jump at any time. Localisation
publishes `map` → `odom` rather than `map` → `base_link`, specifically so the
correction is applied in one place.

**Then why that matters, with the number.** I simulated twenty metres with two
per cent slip and periodic fixes. The `odom` frame's error never moved more than
6.5 mm in a step; the `map` frame's jumped 120 mm when a fix landed. A
controller differentiating position to get velocity sees 1.2 m/s of phantom
velocity on a robot doing 1.0, so a 120 per cent error, with every component
behaving correctly. The rule is to differentiate `odom`, navigate in `map`, and
never mix them in one calculation, and that sentence is what most API
documentation leaves the reader to infer.

**The documentation point I would raise in a planning meeting.** A simulator can
be configured with perfect localisation, which makes the distinction above
invisible. So a tutorial that is correct, reproducible and verified in CI can
teach a model that fails on hardware, and nothing in the pipeline notices. That
is the sim-to-real gap as a documentation problem rather than a physics one, and
the mitigation is editorial: mark which claims were verified on hardware.

**What I would not claim.** No ROS, no Isaac Sim, no robot. The frame reasoning
and the simulated demonstration are mine; the operating experience is not, and
`context` tier is the accurate label.

## How to prove it

**The artifact.** A short simulation showing the two frames' properties, and a
page stating which frame answers which question.

**Three things to do, in order:**

1. Run step 2 and predict which frame has the larger single-step change before
   you look. People reliably guess the drifting one.
2. Take any robotics tutorial you have and check whether it says which frame
   its poses are in. Most say "the pose" and mean one of two incompatible
   things.
3. Check whether a sample that times anything reads the simulation clock or the
   system clock. Under a simulator that can pause, the difference is not subtle.

**What makes it credible rather than decorative.** REP 105's frame names,
ordering, continuity guarantees and transform ownership were verified by opening
the specification, and the drift-against-jump measurement is a short script that
ran here. What is absent is the entire stack: no ROS installation, no Isaac Sim,
no USD robot description driven through a simulator, and no hardware. The
[demonstrated](../demonstrated.md) page records this concept as having no
demonstration in either repository.

## Related

- [OpenUSD and Omniverse](usd-omniverse.md), the scene description Isaac Sim is built on
- [Real-time and graphics systems](realtime-systems.md), the deadline half of the same domain
- [GPU computing and CUDA](gpu-computing.md), what the simulator runs on
- [Code-sample validation](code-sample-validation.md), why a CI-green tutorial can still teach the wrong model

## Sources

- [REP 105, Coordinate Frames for Mobile Platforms](https://reps.openrobotics.org/rep-0105/), opened and read for the frame names, the single-parent tree, the continuity guarantees and the ownership of each transform.
