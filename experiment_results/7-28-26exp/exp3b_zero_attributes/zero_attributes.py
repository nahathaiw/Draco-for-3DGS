#!/usr/bin/env python3
"""Use GS-Interface to zero only the selected Experiment 3B properties."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

GS_INTERFACE_DIR = Path(__file__).resolve().parents[3] / "GS-Interface"
if not (GS_INTERFACE_DIR / "io_3dgs.py").is_file():
    raise FileNotFoundError(f"GS-Interface not found at {GS_INTERFACE_DIR}")
sys.path.insert(0, str(GS_INTERFACE_DIR))

from io_3dgs import GaussianModelV2


TARGET_PROPERTIES = (
    "x", "y", "z",
    "nx", "ny", "nz",
    "scale_0", "scale_1", "scale_2",
    "rot_0", "rot_1", "rot_2", "rot_3",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise ValueError("Refusing to overwrite the source PLY")

    model = GaussianModelV2(str(args.input))
    property_order_before = list(model.data)
    missing = [name for name in TARGET_PROPERTIES if name not in model.data]
    if missing:
        raise ValueError(f"Required properties are missing: {missing}")

    untouched_before = {
        name: value["data"].copy()
        for name, value in model.data.items()
        if name not in TARGET_PROPERTIES
    }

    for name in TARGET_PROPERTIES:
        model.data[name]["data"].fill(np.float32(0.0))

    for name in TARGET_PROPERTIES:
        if not np.all(model.data[name]["data"] == np.float32(0.0)):
            raise RuntimeError(f"Failed to zero {name}")
    for name, expected in untouched_before.items():
        if not np.array_equal(model.data[name]["data"], expected):
            raise RuntimeError(f"Unexpected in-memory change to {name}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.export_gs_to_ply(str(args.output), ascii=False)

    reloaded = GaussianModelV2(str(args.output))
    if reloaded.num_of_point != model.num_of_point:
        raise RuntimeError("Gaussian count changed after export")
    if list(reloaded.data) != property_order_before:
        raise RuntimeError("Property names or order changed after export")
    for name in TARGET_PROPERTIES:
        if not np.all(reloaded.data[name]["data"] == np.float32(0.0)):
            raise RuntimeError(f"Reloaded property is not zero: {name}")
    for name, expected in untouched_before.items():
        if not np.array_equal(reloaded.data[name]["data"], expected):
            raise RuntimeError(f"Untargeted property changed after export: {name}")

    print(json.dumps({
        "input": str(args.input),
        "output": str(args.output),
        "gaussian_count": model.num_of_point,
        "property_count": len(model.data),
        "zeroed_properties": list(TARGET_PROPERTIES),
        "untargeted_properties_preserved": True,
        "property_order_preserved": True,
        "reloaded_output_verified": True,
    }, indent=2))


if __name__ == "__main__":
    main()
