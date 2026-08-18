#!/usr/bin/env python3
"""Independent, standard-library verification for Experiment 3B binary PLYs."""

import argparse
import json
import struct
from pathlib import Path


TARGETS = {
    "x", "y", "z", "nx", "ny", "nz",
    "scale_0", "scale_1", "scale_2",
    "rot_0", "rot_1", "rot_2", "rot_3",
}


def open_ply(path):
    stream = path.open("rb")
    header_lines = []
    while True:
        line = stream.readline()
        if not line:
            raise ValueError(f"{path}: missing end_header")
        header_lines.append(line)
        if line.rstrip() == b"end_header":
            break
    header = b"".join(header_lines).decode("ascii")
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
            raise ValueError(f"{path}: unsupported vertex property: {line}")
    if count is None:
        raise ValueError(f"{path}: missing vertex count")
    return stream, header, count, properties


def compare_source_to_modified(source_path, modified_path):
    source, _, source_count, source_props = open_ply(source_path)
    modified, _, modified_count, modified_props = open_ply(modified_path)
    if source_props != modified_props:
        raise ValueError("Source and modified property names/order differ")
    if source_count != modified_count:
        raise ValueError("Source and modified Gaussian counts differ")
    missing = sorted(TARGETS - set(source_props))
    if missing:
        raise ValueError(f"Missing targets: {missing}")

    row = struct.Struct("<" + "f" * len(source_props))
    target_stats = {
        name: {"source_nonzero": 0, "modified_nonzero": 0, "changed": 0}
        for name in source_props if name in TARGETS
    }
    untargeted_changed = {name: 0 for name in source_props if name not in TARGETS}

    for _ in range(source_count):
        source_bytes = source.read(row.size)
        modified_bytes = modified.read(row.size)
        if len(source_bytes) != row.size or len(modified_bytes) != row.size:
            raise ValueError("Truncated vertex data")
        source_values = row.unpack(source_bytes)
        modified_values = row.unpack(modified_bytes)
        for index, name in enumerate(source_props):
            a_bits = source_bytes[index * 4:(index + 1) * 4]
            b_bits = modified_bytes[index * 4:(index + 1) * 4]
            if name in TARGETS:
                target_stats[name]["source_nonzero"] += int(source_values[index] != 0.0)
                target_stats[name]["modified_nonzero"] += int(modified_values[index] != 0.0)
                target_stats[name]["changed"] += int(a_bits != b_bits)
            else:
                untargeted_changed[name] += int(a_bits != b_bits)
    source.close()
    modified.close()

    return {
        "gaussian_count": source_count,
        "property_count": len(source_props),
        "property_order_preserved": True,
        "targets": target_stats,
        "all_target_outputs_zero": all(
            item["modified_nonzero"] == 0 for item in target_stats.values()
        ),
        "untargeted_changed_values": sum(untargeted_changed.values()),
        "untargeted_properties_bit_exact": all(
            changed == 0 for changed in untargeted_changed.values()
        ),
    }


def compare_modified_to_decoded(modified_path, decoded_path):
    modified, modified_header, modified_count, modified_props = open_ply(modified_path)
    decoded, decoded_header, decoded_count, decoded_props = open_ply(decoded_path)
    if modified_props != decoded_props or modified_count != decoded_count:
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
    result = {
        "source_to_modified": compare_source_to_modified(args.source, args.modified)
    }
    if args.decoded:
        result["modified_to_decoded"] = compare_modified_to_decoded(
            args.modified, args.decoded
        )
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
