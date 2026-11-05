#!/usr/bin/env python3
"""Two coordinate frames that disagree on purpose, and why.

    pip install numpy && python3 drills/frames.py

ROS REP 105 gives `odom` and `map` opposite guarantees: `odom` is continuous and
drifts without bound, `map` is accurate and changes in discrete jumps. This
simulates both so the reason is visible. It is not ROS, and no robot or
simulator is involved.
"""

from __future__ import annotations

import numpy as np

STEPS = 200
DT = 0.1          # seconds per step
VELOCITY = 1.0    # metres per second
SLIP = 0.02       # wheel-odometry error, as a fraction
FIX_EVERY = 25    # steps between localisation fixes
FIX_NOISE = 0.03  # metres


def simulate(seed: int = 7) -> tuple[list[float], list[float]]:
    rng = np.random.default_rng(seed)
    truth = odom = map_est = 0.0
    odom_err, map_err = [], []
    for step in range(STEPS):
        truth += VELOCITY * DT
        # Odometry integrates its own error: smooth, and unbounded.
        odom += VELOCITY * DT * (1 + rng.normal(0, SLIP))
        if (step + 1) % FIX_EVERY == 0:
            # A localisation fix lands: accurate, and discontinuous.
            map_est = truth + rng.normal(0, FIX_NOISE)
        else:
            map_est += VELOCITY * DT * (1 + rng.normal(0, SLIP))
        odom_err.append(odom - truth)
        map_err.append(map_est - truth)
    return odom_err, map_err


def largest_step(series: list[float]) -> float:
    return max(abs(b - a) for a, b in zip(series, series[1:]))


def main() -> None:
    odom_err, map_err = simulate()
    print("%d steps, %.0f m travelled, %.0f per cent slip, a fix every %d steps\n"
          % (STEPS, STEPS * DT * VELOCITY, SLIP * 100, FIX_EVERY))
    print("%-30s %12s %12s" % ("", "odom frame", "map frame"))
    print("%-30s %10.3f m %10.3f m" % ("error at the end", odom_err[-1], map_err[-1]))
    print("%-30s %10.3f m %10.3f m"
          % ("worst error", max(map(abs, odom_err)), max(map(abs, map_err))))
    jump_odom, jump_map = largest_step(odom_err), largest_step(map_err)
    print("%-30s %10.4f m %10.4f m" % ("largest single-step change", jump_odom, jump_map))

    print("\nodom: drifts, smoothly, without bound. Never jumps.")
    print("map:  bounded error, and jumps %.3f m the instant a fix lands." % jump_map)
    print("\nA controller differentiating position to get velocity sees")
    print("%.1f m/s of phantom velocity on a robot travelling %.1f m/s."
          % (jump_map / DT, VELOCITY))
    print("\nSo: differentiate odom, navigate in map, never mix them in one")
    print("calculation. REP 105 implies it; saying it outright is the")
    print("documentation contribution.")


if __name__ == "__main__":
    main()
