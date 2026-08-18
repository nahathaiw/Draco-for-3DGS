#!/usr/bin/env python3
"""Compare two binary little-endian float32 3DGS PLY files by row and property."""

import argparse
import json
import math
import struct
from pathlib import Path


def read_header(stream):
    lines = []
    while True:
        line = stream.readline()
        if not line:
            raise ValueError("PLY header has no end_header")
        lines.append(line)
        if line.rstrip() == b"end_header":
            break
    text = b"".join(lines).decode("ascii")
    if "format binary_little_endian 1.0" not in text:
        raise ValueError("Only binary little-endian PLY is supported")
    count = None
    properties = []
    in_vertex = False
    for line in text.splitlines():
        fields = line.split()
        if fields[:2] == ["element", "vertex"]:
            count = int(fields[2])
            in_vertex = True
        elif fields[:1] == ["element"]:
            in_vertex = False
        elif in_vertex and fields[:2] == ["property", "float"]:
            properties.append(fields[2])
        elif in_vertex and fields[:1] == ["property"]:
            raise ValueError(f"Unsupported vertex property: {line}")
    if count is None or not properties:
        raise ValueError("Missing vertex element or float properties")
    return text, count, properties


def group(name):
    if name in ("x", "y", "z"):
        return "position"
    if name in ("nx", "ny", "nz"):
        return "normal"
    if name.startswith("f_dc_"):
        return "f_dc"
    if name.startswith("f_rest_"):
        index = int(name.removeprefix("f_rest_"))
        return "f_rest_1" if index < 9 else "f_rest_2" if index < 24 else "f_rest_3"
    if name == "opacity":
        return "opacity"
    if name.startswith("scale_"):
        return "scale"
    if name.startswith("rot_"):
        return "rotation"
    return "other"


def compare(original_path, decoded_path):
    with original_path.open("rb") as original, decoded_path.open("rb") as decoded:
        original_header, original_count, original_properties = read_header(original)
        decoded_header, decoded_count, decoded_properties = read_header(decoded)
        if original_properties != decoded_properties:
            raise ValueError("Property names/order differ")
        if original_count != decoded_count:
            raise ValueError("Gaussian counts differ")

        row = struct.Struct("<" + "f" * len(original_properties))
        stats = {}
        for name in original_properties:
            stats.setdefault(group(name), {
                "value_count": 0, "changed_values": 0, "max_abs_error": 0.0,
                "sum_abs_error": 0.0, "sum_squared_error": 0.0,
            })

        rows_with_position_difference = 0
        for _ in range(original_count):
            original_bytes = original.read(row.size)
            decoded_bytes = decoded.read(row.size)
            if len(original_bytes) != row.size or len(decoded_bytes) != row.size:
                raise ValueError("Truncated vertex data")
            original_values = row.unpack(original_bytes)
            decoded_values = row.unpack(decoded_bytes)
            position_differs = False
            for index, name in enumerate(original_properties):
                category = group(name)
                summary = stats[category]
                a, b = original_values[index], decoded_values[index]
                same_bits = original_bytes[index * 4:(index + 1) * 4] == decoded_bytes[index * 4:(index + 1) * 4]
                error = 0.0 if same_bits else abs(a - b)
                summary["value_count"] += 1
                summary["changed_values"] += int(not same_bits)
                summary["max_abs_error"] = max(summary["max_abs_error"], error)
                summary["sum_abs_error"] += error
                summary["sum_squared_error"] += error * error
                if category == "position" and not same_bits:
                    position_differs = True
            rows_with_position_difference += int(position_differs)

        if original.read(1) or decoded.read(1):
            raise ValueError("Unexpected data after vertex records")

    for summary in stats.values():
        count = summary["value_count"]
        summary["mae"] = summary.pop("sum_abs_error") / count
        summary["rmse"] = math.sqrt(summary.pop("sum_squared_error") / count)
        summary["exact"] = summary["changed_values"] == 0

    non_sh = ("position", "normal", "opacity", "scale", "rotation")
    return {
        "original": str(original_path),
        "decoded": str(decoded_path),
        "gaussian_count_original": original_count,
        "gaussian_count_decoded": decoded_count,
        "property_count": len(original_properties),
        "property_order_identical": original_properties == decoded_properties,
        "rows_with_position_difference": rows_with_position_difference,
        "ordering_preserved_by_position": rows_with_position_difference == 0,
        "non_sh_exact": all(stats[name]["exact"] for name in non_sh),
        "header_identical": original_header == decoded_header,
        "groups": stats,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("decoded", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = compare(args.original, args.decoded)
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
