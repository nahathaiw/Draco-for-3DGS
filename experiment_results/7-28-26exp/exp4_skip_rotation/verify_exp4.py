#!/usr/bin/env python3
"""Verify retained PLY properties after optional Draco attribute omission."""

import argparse
import json
import struct
from pathlib import Path


def open_ply(path):
    stream = path.open("rb")
    lines = []
    while True:
        line = stream.readline()
        if not line:
            raise ValueError(f"{path}: missing end_header")
        lines.append(line)
        if line.rstrip() == b"end_header":
            break
    header = b"".join(lines).decode("ascii")
    if "format binary_little_endian 1.0" not in header:
        raise ValueError(f"{path}: expected binary little-endian PLY")
    count = None
    properties = []
    in_vertex = False
    for line in header.splitlines():
        fields = line.split()
        if fields[:2] == ["element", "vertex"]:
            count = int(fields[2])
            in_vertex = True
        elif fields[:1] == ["element"]:
            in_vertex = False
        elif in_vertex and fields[:2] == ["property", "float"]:
            properties.append(fields[2])
        elif in_vertex and fields[:1] == ["property"]:
            raise ValueError(f"{path}: unsupported property: {line}")
    if count is None:
        raise ValueError(f"{path}: missing vertex count")
    return stream, header, count, properties


def property_group(name):
    if name in ("x", "y", "z"):
        return "position_xyz"
    if name.startswith("f_dc_"):
        return "color_f_dc"
    if name.startswith("f_rest_"):
        return "color_f_rest"
    return "other_retained"


def verify(source_path, decoded_path, expected_missing):
    source, source_header, source_count, source_props = open_ply(source_path)
    decoded, decoded_header, decoded_count, decoded_props = open_ply(decoded_path)
    actual_missing = [name for name in source_props if name not in decoded_props]
    unexpected_extra = [name for name in decoded_props if name not in source_props]
    expected_retained = [
        name for name in source_props if name not in expected_missing
    ]
    if decoded_props != expected_retained:
        raise ValueError(
            "Decoded property order does not equal source order minus expected omissions"
        )

    source_row = struct.Struct("<" + "f" * len(source_props))
    decoded_row = struct.Struct("<" + "f" * len(decoded_props))
    source_indexes = {name: index for index, name in enumerate(source_props)}
    changed_values = 0
    changed_rows = 0
    property_changed_values = {name: 0 for name in decoded_props}
    group_stats = {}
    for name in decoded_props:
        group = property_group(name)
        group_stats.setdefault(group, {"value_count": 0, "changed_values": 0})
        group_stats[group]["value_count"] += source_count

    for _ in range(source_count):
        source_bytes = source.read(source_row.size)
        decoded_bytes = decoded.read(decoded_row.size)
        if (len(source_bytes) != source_row.size or
                len(decoded_bytes) != decoded_row.size):
            raise ValueError("Truncated vertex data")
        row_changed = False
        for decoded_index, name in enumerate(decoded_props):
            source_index = source_indexes[name]
            source_bits = source_bytes[source_index * 4:(source_index + 1) * 4]
            decoded_bits = decoded_bytes[decoded_index * 4:(decoded_index + 1) * 4]
            if source_bits != decoded_bits:
                changed_values += 1
                property_changed_values[name] += 1
                group_stats[property_group(name)]["changed_values"] += 1
                row_changed = True
        changed_rows += int(row_changed)

    source_trailing = bool(source.read(1))
    decoded_trailing = bool(decoded.read(1))
    source.close()
    decoded.close()

    return {
        "source": str(source_path),
        "decoded": str(decoded_path),
        "source_gaussian_count": source_count,
        "decoded_gaussian_count": decoded_count,
        "gaussian_count_preserved": source_count == decoded_count,
        "source_property_count": len(source_props),
        "decoded_property_count": len(decoded_props),
        "expected_missing_properties": expected_missing,
        "actual_missing_properties": actual_missing,
        "missing_properties_match_expectation": actual_missing == expected_missing,
        "unexpected_extra_properties": unexpected_extra,
        "retained_property_order_preserved": decoded_props == expected_retained,
        "retained_changed_rows": changed_rows,
        "retained_changed_values": changed_values,
        "all_retained_float32_values_bit_exact": changed_values == 0,
        "focused_groups": {
            name: {
                **group_stats[name],
                "bit_exact": group_stats[name]["changed_values"] == 0,
            }
            for name in ("position_xyz", "color_f_dc", "color_f_rest")
        },
        "focused_property_changed_values": {
            name: property_changed_values[name]
            for name in decoded_props
            if property_group(name) != "other_retained"
        },
        "header_identical": source_header == decoded_header,
        "unexpected_trailing_data": source_trailing or decoded_trailing,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--decoded", required=True, type=Path)
    parser.add_argument("--expect-missing", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.source, args.decoded, args.expect_missing)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
