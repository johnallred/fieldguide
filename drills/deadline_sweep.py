#!/usr/bin/env python3
"""The same work against tightening deadlines: a flat median hiding 30% misses.

    python3 drills/deadline_sweep.py

In a real-time system a missed deadline is a failure rather than a slowdown, so
the mean and the median cannot express the failure mode. Watch the p50 column
stay flat while the miss count goes from 0 to 74 of 250.
"""

from __future__ import annotations

import statistics
import time

CYCLES = 250
WORK = 30_000  # iterations of arithmetic, sized so one cycle is ~1.4 ms


def do_work() -> None:
    sum(x * x for x in range(WORK))


def measure_work_alone(samples: int = 40) -> float:
    out = []
    for _ in range(samples):
        t = time.perf_counter()
        do_work()
        out.append((time.perf_counter() - t) * 1000)
    return statistics.fmean(out)


def run(period_ms: float) -> list[float]:
    """Return each cycle's completion time, relative to its own deadline."""
    completions = []
    start = time.perf_counter()
    for i in range(CYCLES):
        target = start + (i + 1) * period_ms / 1000
        now = time.perf_counter()
        if target > now:
            time.sleep(target - now)
        do_work()
        completions.append((time.perf_counter() - target) * 1000)
    return completions


def main() -> None:
    print("the work itself: mean %.3f ms per cycle\n" % measure_work_alone())
    print("  period  misses        completion time (ms)")
    print("    (ms)              mean     p50     p99     max")
    for period in (10.0, 5.0, 2.0, 1.5, 1.0):
        done = run(period)
        s = sorted(done)
        missed = sum(1 for d in done if d > period)
        print("  %6.1f  %4d/%d  %7.3f %7.3f %7.3f %7.3f"
              % (period, missed, CYCLES, statistics.fmean(done),
                 s[CYCLES // 2], s[int(CYCLES * 0.99) - 1], s[-1]))
    print("\nBetween two of those rows the system does not degrade, it collapses:")
    print("once the work cannot fit in the period, every cycle starts later than")
    print("the last and the lag compounds without bound.")


if __name__ == "__main__":
    main()
