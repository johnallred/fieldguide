#!/usr/bin/env python3
"""Which USD opinion wins: layer strength, and the ordering people get backwards.

    pip install usd-core && python3 drills/usd_composition.py

Run in an empty directory; it writes .usda files beside itself.
"""

from __future__ import annotations

from pxr import Sdf, Usd, UsdGeom


def override_leaves_the_base_untouched() -> None:
    """A studio edits a vendor's asset without editing the vendor's file."""
    base = Usd.Stage.CreateNew("base.usda")
    arm = UsdGeom.Cube.Define(base, "/Robot/Arm")
    arm.GetPrim().CreateAttribute("payload_kg", Sdf.ValueTypeNames.Float).Set(2.5)
    base.GetRootLayer().Save()

    over = Usd.Stage.CreateNew("studio.usda")
    over.GetRootLayer().subLayerPaths = ["./base.usda"]
    ov = over.OverridePrim("/Robot/Arm")
    ov.CreateAttribute("payload_kg", Sdf.ValueTypeNames.Float).Set(4.0)
    over.GetRootLayer().Save()

    stage = Usd.Stage.Open("studio.usda")
    attr = stage.GetPrimAtPath("/Robot/Arm").GetAttribute("payload_kg")
    print("base.usda        payload_kg = 2.5")
    print("studio.usda      payload_kg = %.1f   <- the override wins" % attr.Get())
    print("\nbase file on disk, unchanged:")
    print("  " + "\n  ".join(l for l in open("base.usda").read().splitlines() if "payload" in l))

    # The single most useful debugging call in the API.
    print("\nwhere the winning value comes from:")
    for spec in attr.GetPropertyStack(Usd.TimeCode.Default()):
        print("  %-28s %s" % (spec.layer.identifier.split("/")[-1], spec.default))


def the_first_sublayer_wins() -> None:
    """The ordering that violates every other ordering a developer knows.

    CSS, `#include`, shell `source`, dict.update and Docker layers are all
    later-wins. `subLayerPaths` is strongest-first, so a reader who assumes
    otherwise gets a silently wrong scene and no error anywhere.
    """
    for name, val in [("a.usda", 10.0), ("b.usda", 20.0)]:
        s = Usd.Stage.CreateNew(name)
        p = UsdGeom.Xform.Define(s, "/Robot")
        p.GetPrim().CreateAttribute("speed", Sdf.ValueTypeNames.Float).Set(val)
        s.GetRootLayer().Save()

    for root_name, order in [("root.usda", ["./a.usda", "./b.usda"]),
                             ("root2.usda", ["./b.usda", "./a.usda"])]:
        root = Usd.Stage.CreateNew(root_name)
        root.GetRootLayer().subLayerPaths = order
        root.GetRootLayer().Save()
        attr = Usd.Stage.Open(root_name).GetPrimAtPath("/Robot").GetAttribute("speed")
        print("\nsubLayerPaths = %s   a sets 10, b sets 20" % order)
        print("  resolved speed = %.0f" % attr.Get())
        for spec in attr.GetPropertyStack(Usd.TimeCode.Default()):
            print("    %-12s %s" % (spec.layer.identifier.split("/")[-1], spec.default))


def local_beats_a_reference() -> None:
    """LIVRPS: Local, Inherits, VariantSets, References, Payloads, Specialises."""
    src = Usd.Stage.CreateNew("asset.usda")
    a = UsdGeom.Xform.Define(src, "/Asset")
    a.GetPrim().CreateAttribute("mass", Sdf.ValueTypeNames.Float).Set(100.0)
    src.GetRootLayer().Save()

    st = Usd.Stage.CreateNew("scene.usda")
    inst = UsdGeom.Xform.Define(st, "/Scene/Instance")
    inst.GetPrim().GetReferences().AddReference("./asset.usda", "/Asset")
    print("\nreference only:          mass = %.0f" % inst.GetPrim().GetAttribute("mass").Get())
    inst.GetPrim().CreateAttribute("mass", Sdf.ValueTypeNames.Float).Set(7.0)
    print("local opinion added:     mass = %.0f   <- local beats the reference"
          % inst.GetPrim().GetAttribute("mass").Get())


if __name__ == "__main__":
    override_leaves_the_base_untouched()
    the_first_sublayer_wins()
    local_beats_a_reference()
