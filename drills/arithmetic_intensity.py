#!/usr/bin/env python3
"""Why performance follows data movement rather than arithmetic.

    pip install numpy && python3 drills/arithmetic_intensity.py

This runs on a CPU and demonstrates a GPU lesson by analogy. The ratio argument
transfers: an operation reusing each loaded byte once is waiting for memory, and
a processor with more arithmetic units will not help it. None of the absolute
numbers transfer, and a GPU's coalescing rules, occupancy and memory hierarchy
are not modelled here at all.
"""

from __future__ import annotations

import time

import numpy as np

N = 2048


def best_of(fn, repeats: int = 7) -> float:
    fn()  # warm
    best = float("inf")
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t)
    return best


def main() -> None:
    a = np.random.randn(N, N).astype(np.float32)
    b = np.random.randn(N, N).astype(np.float32)
    c = np.empty_like(a)
    word = 4  # float32

    ops = [
        ("copy        A -> C", lambda: np.copyto(c, a), 2 * N * N * word, 0),
        ("add         A + B", lambda: np.add(a, b, out=c), 3 * N * N * word, N * N),
        ("scale+add   2A + B", lambda: np.add(2 * a, b, out=c), 4 * N * N * word, 2 * N * N),
        ("matmul      A @ B", lambda: np.matmul(a, b, out=c), 3 * N * N * word, 2 * N ** 3),
    ]

    print("%-22s %9s %10s %12s %10s" % ("operation", "ms", "GB/s", "GFLOP/s", "flops/byte"))
    for label, fn, nbytes, nflops in ops:
        t = best_of(fn)
        print("%-22s %9.2f %10.1f %12.1f %10.2f"
              % (label, t * 1000, nbytes / t / 1e9, nflops / t / 1e9, nflops / nbytes))

    print("\nThe elementwise rows sit at the memory ceiling and achieve about one")
    print("GFLOP/s. The matmul achieves a hundred times more on the same arrays,")
    print("because it reuses each loaded byte hundreds of times.")
    print("\n  arithmetic intensity = flops / bytes moved")
    print("  intensity < device_flops / device_bandwidth  ->  memory bound")


if __name__ == "__main__":
    main()
