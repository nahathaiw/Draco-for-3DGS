#!/usr/bin/env python3
"""Verify Experiment 3C modification and lossless Draco round trip."""

import argparse
import json
import struct
from pathlib import Path


IDENTITY = {"rot_0": 1.0, "rot_1": 0.0, "rot_2": 0.0, "rot_3": 0.0}


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
    return stream, header, count, properties


def source_to_modified(source_path, modified_path):
    source, _, source_count, source_props = open_ply(source_path)
    modified, _, modified_count, modified_props = open_ply(modified_path)
    if source_count != modified_count or source_props != modified_props:
        raise ValueError("Source and modified schema/count differ")
    row = struct.Struct("<" + "f" * len(source_props))
    rotation_stats = {
        name: {"expected": expected, "incorrect_outputs": 0, "changed_values": 0}
        for name, expected in IDENTITY.items()
    }
    untargeted_changed = 0
    for _ in range(source_count):
        a = source.read(row.size)
        b = modified.read(row.size)
        if len(a) != row.size or len(b) != row.size:
            raise ValueError("Truncated vertex data")
        b_values = row.unpack(b)
        for index, name in enumerate(source_props):
            a_bits = a[index * 4:(index + 1) * 4]
            b_bits = b[index * 4:(index + 1) * 4]
            if name in IDENTITY:
                rotation_stats[name]["incorrect_outputs"] += int(
                    b_values[index] != IDENTITY[name]
                )
                rotation_stats[name]["changed_values"] += int(a_bits != b_bits)
            else:
                untargeted_changed += int(a_bits != b_bits)
    source.close()
    modified.close()
    return {
        "gaussian_count": source_count,
        "property_count": len(source_props),
        "property_order_preserved": True,
        "rotation": rotation_stats,
        "identity_rotation_exact": all(
            item["incorrect_outputs"] == 0 for item in rotation_stats.values()
        ),
        "untargeted_changed_values": untargeted_changed,
        "untargeted_values_bit_exact": untargeted_changed == 0,
    }


def modified_to_decoded(modified_path, decoded_path):
    modified, modified_header, modified_count, modified_props = open_ply(modified_path)
    decoded, decoded_header, decoded_count, decoded_props = open_ply(decoded_path)
    if modified_count != decoded_count or modified_props != decoded_props:
        raise ValueError("Modified and decoded schema/count differ")
    row_size = 4 * len(modified_props)
    changed_rows = 0
    changed_values = 0
    for _ in range(modified_count):
        a = modified.read(row_size)
        b = decoded.read(row_size)
        if len(a) != row_size or len(b) != row_size:
            raise ValueError("Truncated vertex data")
        changed_rows += int(a != b)
        changed_values += sum(
            a[index:index + 4] != b[index:index + 4]
            for index in range(0, row_size, 4)
        )
    modified.close()
    decoded.close()
    return {
        "gaussian_count_preserved": modified_count == decoded_count,
        "property_order_preserved": modified_props == decoded_props,
        "header_identical": modified_header == decoded_header,
        "changed_rows": changed_rows,
        "changed_values": changed_values,
        "all_float32_values_bit_exact": changed_values == 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--modified", required=True, type=Path)
    parser.add_argument("--decoded", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {"source_to_modified": source_to_modified(args.source, args.modified)}
    if args.decoded:
        result["modified_to_decoded"] = modified_to_decoded(
            args.modified, args.decoded
        )
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
