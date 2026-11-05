#!/usr/bin/env python3
"""Latency against throughput, and the batch size past which batching is loss.

    pip install onnx onnxruntime && python3 drills/inference_sweep.py

The last column is the one benchmarks omit: a request arriving into a batching
server waits for the batch to fill before any compute happens, so the latency
it experiences is that wait plus the batch time. Per-request compute time is
arithmetically true and is not what any request experiences.
"""

from __future__ import annotations

import time

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper

D, H = 1024, 4096
ARRIVAL_RATE = 500.0  # requests per second, for the queue-wait column


def build(path: str) -> None:
    def weights(name, rows, cols):
        data = np.random.randn(rows * cols).astype(np.float32).tobytes()
        return helper.make_tensor(name, TensorProto.FLOAT, [rows, cols], data, raw=True)

    graph = helper.make_graph(
        [helper.make_node("MatMul", ["x", "w1"], ["h"]),
         helper.make_node("Relu", ["h"], ["hr"]),
         helper.make_node("MatMul", ["hr", "w2"], ["y"])],
        "mlp",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, ["batch", D])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, ["batch", D])],
        [weights("w1", D, H), weights("w2", H, D)],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    # onnx writes IR 14 by default and onnxruntime refuses it; see onnx_compat.py.
    model.ir_version = 10
    onnx.save(model, path)


def median_batch_ms(sess, batch: int, n: int = 25) -> float:
    x = np.random.randn(batch, D).astype(np.float32)
    sess.run(None, {"x": x})  # warm: the first call is not representative
    times = []
    for _ in range(n):
        t = time.perf_counter()
        sess.run(None, {"x": x})
        times.append((time.perf_counter() - t) * 1000)
    return sorted(times)[len(times) // 2]


def main() -> None:
    build("mlp.onnx")
    print("model: %.1f MB of weights, two %dx%d matmuls\n" % (2 * D * H * 4 / 1e6, D, H))
    sess = ort.InferenceSession("mlp.onnx", providers=["CPUExecutionProvider"])

    print("  batch  batch ms   per-req ms   throughput   wait for a full batch   total latency")
    print("                    (compute)      req/s      at %.0f req/s             p50 ms" % ARRIVAL_RATE)
    for batch in (1, 2, 4, 8, 16, 32, 64):
        med = median_batch_ms(sess, batch)
        wait = (batch - 1) / ARRIVAL_RATE * 1000
        print("  %5d  %8.2f %10.2f %12.0f %18.1f %15.1f"
              % (batch, med, med / batch, batch / (med / 1000), wait, wait + med))
    print("\nThroughput stops improving at the knee; latency does not stop rising.")


if __name__ == "__main__":
    main()
