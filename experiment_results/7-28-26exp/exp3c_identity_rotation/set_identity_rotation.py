#!/usr/bin/env python3
"""Set every Gaussian to the identity rotation using GS-Interface."""

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


ROTATION_VALUES = {
    "rot_0": np.float32(1.0),
    "rot_1": np.float32(0.0),
    "rot_2": np.float32(0.0),
    "rot_3": np.float32(0.0),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise ValueError("Refusing to overwrite the source PLY")

    model = GaussianModelV2(str(args.input))
    order_before = list(model.data)
    missing = [name for name in ROTATION_VALUES if name not in model.data]
    if missing:
        raise ValueError(f"Required properties are missing: {missing}")

    untouched_before = {
        name: value["data"].copy()
        for name, value in model.data.items()
        if name not in ROTATION_VALUES
    }
    for name, value in ROTATION_VALUES.items():
        model.data[name]["data"].fill(value)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.export_gs_to_ply(str(args.output), ascii=False)
    reloaded = GaussianModelV2(str(args.output))

    if reloaded.num_of_point != model.num_of_point:
        raise RuntimeError("Gaussian count changed")
    if list(reloaded.data) != order_before:
        raise RuntimeError("Property names or order changed")
    for name, expected in ROTATION_VALUES.items():
        if not np.all(reloaded.data[name]["data"] == expected):
            raise RuntimeError(f"Incorrect identity value in {name}")
    for name, expected in untouched_before.items():
        if not np.array_equal(reloaded.data[name]["data"], expected):
            raise RuntimeError(f"Untargeted property changed: {name}")

    print(json.dumps({
        "input": str(args.input),
        "output": str(args.output),
        "gaussian_count": model.num_of_point,
        "property_count": len(model.data),
        "rotation": {name: float(value) for name, value in ROTATION_VALUES.items()},
        "untargeted_properties_preserved": True,
        "property_order_preserved": True,
        "reloaded_output_verified": True,
    }, indent=2))


if __name__ == "__main__":
    main()
