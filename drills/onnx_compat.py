#!/usr/bin/env python3
"""Two current packages, one two-line model, four different outcomes.

    pip install onnx onnxruntime && python3 drills/onnx_compat.py

The default output of the newest `onnx` is not loadable by the newest
`onnxruntime`: opset and IR version are separate axes and fail differently, and
an opset that is too old fails at a later stage than one that is too new.
"""

from __future__ import annotations

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper


def model(path: str, opset: int, ir: int | None = None) -> int:
    graph = helper.make_graph(
        [helper.make_node("Relu", ["x"], ["y"])],
        "g",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2])],
    )
    m = helper.make_model(graph, opset_imports=[helper.make_opsetid("", opset)])
    if ir is not None:
        m.ir_version = ir
    onnx.save(m, path)
    return m.ir_version


def main() -> None:
    print("installed:")
    print("  onnx          %s   (writes IR %d, knows opset %d)"
          % (onnx.__version__, onnx.IR_VERSION, onnx.defs.onnx_opset_version()))
    print("  onnxruntime   %s\n" % ort.__version__)

    default_ir = model("default.onnx", 17)
    print("make_model default ir_version = %d" % default_ir)

    print("\n%-26s %s" % ("model as written", "what onnxruntime does with it"))
    cases = [("opset 17, IR 10", 17, 10),
             ("opset 28, IR 10", 28, 10),
             ("opset 17, IR %d (default)" % default_ir, 17, None),
             ("opset 1,  IR 10", 1, 10)]
    for label, opset, ir in cases:
        model("t.onnx", opset, ir)
        try:
            sess = ort.InferenceSession("t.onnx", providers=["CPUExecutionProvider"])
            sess.run(None, {"x": np.array([1.0, -1.0], dtype=np.float32)})
            print("%-26s loads and runs" % label)
        except Exception as exc:  # noqa: BLE001 - the message is the finding
            print("%-26s %s" % (label, " ".join(str(exc).split())[:120]))

    print("\nThe fix for the IR case is one line, `m.ir_version = 10`, and it is")
    print("not in any of those messages.")


if __name__ == "__main__":
    main()
