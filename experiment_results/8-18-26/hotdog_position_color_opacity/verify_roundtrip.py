#!/usr/bin/env python3
"""Verify exact retained attributes in a binary float32 3DGS PLY round trip."""

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


def portable_path(path):
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def read_header(stream):
    header_lines = []
    count = None
    properties = []
    in_vertex = False
    while True:
        raw_line = stream.readline()
        if not raw_line:
            raise ValueError("PLY header has no end_header")
        header_lines.append(raw_line)
        line = raw_line.decode("ascii").rstrip("\r\n")
        fields = line.split()
        if fields[:2] == ["format", "binary_little_endian"]:
            pass
        elif fields[:1] == ["format"]:
            raise ValueError(f"Expected binary_little_endian, found: {line}")
        if fields[:2] == ["element", "vertex"]:
            count = int(fields[2])
            in_vertex = True
        elif fields[:1] == ["element"]:
            if int(fields[2]) != 0:
                raise ValueError(f"Unsupported non-vertex element: {line}")
            in_vertex = False
        elif in_vertex and fields[:2] == ["property", "float"]:
            properties.append(fields[2])
        elif in_vertex and fields[:1] == ["property"]:
            raise ValueError(f"Unsupported property: {line}")
        if line == "end_header":
            break
    if count is None or not properties:
        raise ValueError("Missing vertex element or float properties")
    return b"".join(header_lines), count, properties


def group(name):
    if name in ("x", "y", "z"):
        return "position"
    if name.startswith("f_dc_"):
        return "color_f_dc"
    if name.startswith("f_rest_"):
        return "color_f_rest"
    if name == "opacity":
        return "opacity"
    return "other"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(source_path, decoded_path, expected_missing):
    with source_path.open("rb") as source, decoded_path.open("rb") as decoded:
        source_header, source_count, source_properties = read_header(source)
        decoded_header, decoded_count, decoded_properties = read_header(decoded)
        expected_properties = [
            name for name in source_properties if name not in expected_missing
        ]
        actual_missing = [
            name for name in source_properties if name not in decoded_properties
        ]
        unexpected_extra = [
            name for name in decoded_properties if name not in source_properties
        ]

        source_offsets = {
            name: index * 4 for index, name in enumerate(source_properties)
        }
        decoded_offsets = {
            name: index * 4 for index, name in enumerate(decoded_properties)
        }
        source_row_size = len(source_properties) * 4
        decoded_row_size = len(decoded_properties) * 4
        stats = {
            name: {"value_count": 0, "changed_values": 0}
            for name in ("position", "color_f_dc", "color_f_rest", "opacity")
        }
        retained_changed_rows = 0
        position_changed_rows = 0
        source_non_finite = 0
        decoded_non_finite = 0

        rows_to_compare = min(source_count, decoded_count)
        for row_index in range(rows_to_compare):
            source_row = source.read(source_row_size)
            decoded_row = decoded.read(decoded_row_size)
            if len(source_row) != source_row_size:
                raise ValueError(f"Truncated source row {row_index}")
            if len(decoded_row) != decoded_row_size:
                raise ValueError(f"Truncated decoded row {row_index}")
            row_changed = False
            position_changed = False
            for name in expected_properties:
                if name not in decoded_offsets:
                    continue
                category = group(name)
                if category == "other":
                    continue
                source_offset = source_offsets[name]
                decoded_offset = decoded_offsets[name]
                source_bits = source_row[source_offset:source_offset + 4]
                decoded_bits = decoded_row[decoded_offset:decoded_offset + 4]
                source_value = struct.unpack("<f", source_bits)[0]
                decoded_value = struct.unpack("<f", decoded_bits)[0]
                source_non_finite += int(not math.isfinite(source_value))
                decoded_non_finite += int(not math.isfinite(decoded_value))
                changed = source_bits != decoded_bits
                stats[category]["value_count"] += 1
                stats[category]["changed_values"] += int(changed)
                row_changed = row_changed or changed
                if category == "position":
                    position_changed = position_changed or changed
            retained_changed_rows += int(row_changed)
            position_changed_rows += int(position_changed)

        source_trailing = bool(source.read(1))
        decoded_trailing = bool(decoded.read(1))

    for summary in stats.values():
        summary["bit_exact"] = summary["changed_values"] == 0

    result = {
        "source": portable_path(source_path),
        "decoded": portable_path(decoded_path),
        "source_sha256": sha256(source_path),
        "decoded_sha256": sha256(decoded_path),
        "source_gaussian_count": source_count,
        "decoded_gaussian_count": decoded_count,
        "gaussian_count_preserved": source_count == decoded_count,
        "source_property_count": len(source_properties),
        "decoded_property_count": len(decoded_properties),
        "expected_missing_properties": expected_missing,
        "actual_missing_properties": actual_missing,
        "missing_properties_match_expectation": actual_missing == expected_missing,
        "unexpected_extra_properties": unexpected_extra,
        "retained_property_order_preserved": decoded_properties == expected_properties,
        "retained_changed_rows": retained_changed_rows,
        "position_changed_rows": position_changed_rows,
        "all_retained_float32_values_bit_exact": all(
            summary["bit_exact"] for summary in stats.values()
        ),
        "source_non_finite_retained_values": source_non_finite,
        "decoded_non_finite_retained_values": decoded_non_finite,
        "source_header_identical_to_decoded": source_header == decoded_header,
        "source_trailing_data": source_trailing,
        "decoded_trailing_data": decoded_trailing,
        "groups": stats,
    }
    result["passed"] = all(
        (
            result["gaussian_count_preserved"],
            result["missing_properties_match_expectation"],
            not result["unexpected_extra_properties"],
            result["retained_property_order_preserved"],
            result["all_retained_float32_values_bit_exact"],
            result["source_non_finite_retained_values"] == 0,
            result["decoded_non_finite_retained_values"] == 0,
            not result["source_trailing_data"],
            not result["decoded_trailing_data"],
        )
    )
    return result


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
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
