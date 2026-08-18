#!/usr/bin/env python3
"""Verify that an ASCII PLY contains the exact float32 data of a binary PLY."""

import argparse
import json
import struct
from pathlib import Path


def portable_path(path):
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def read_header(stream, expected_format):
    count = None
    properties = []
    in_vertex = False
    while True:
        raw_line = stream.readline()
        if not raw_line:
            raise ValueError("PLY header has no end_header")
        line = raw_line.decode("ascii").rstrip("\r\n")
        fields = line.split()
        if fields[:2] == ["format", expected_format]:
            pass
        elif fields[:1] == ["format"]:
            raise ValueError(f"Expected {expected_format}, found: {line}")
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
    return count, properties


def verify(binary_path, ascii_path):
    with binary_path.open("rb") as binary, ascii_path.open("rb") as ascii_file:
        binary_count, binary_properties = read_header(
            binary, "binary_little_endian"
        )
        ascii_count, ascii_properties = read_header(ascii_file, "ascii")
        if binary_count != ascii_count:
            raise ValueError("Vertex counts differ")
        if binary_properties != ascii_properties:
            raise ValueError("Property names or ordering differ")

        row_size = len(binary_properties) * 4
        mismatched_values = 0
        mismatched_rows = 0
        for row_index in range(binary_count):
            binary_row = binary.read(row_size)
            if len(binary_row) != row_size:
                raise ValueError(f"Truncated binary row {row_index}")
            ascii_line = ascii_file.readline()
            if not ascii_line:
                raise ValueError(f"Truncated ASCII row {row_index}")
            fields = ascii_line.split()
            if len(fields) != len(binary_properties):
                raise ValueError(
                    f"ASCII row {row_index} has {len(fields)} values; "
                    f"expected {len(binary_properties)}"
                )
            row_changed = False
            for index, field in enumerate(fields):
                ascii_bits = struct.pack("<f", float(field))
                binary_bits = binary_row[index * 4:(index + 1) * 4]
                if ascii_bits != binary_bits:
                    mismatched_values += 1
                    row_changed = True
            mismatched_rows += int(row_changed)

        binary_trailing = bool(binary.read(1))
        ascii_trailing = bool(ascii_file.read().strip())

    result = {
        "binary": portable_path(binary_path),
        "ascii": portable_path(ascii_path),
        "vertex_count": binary_count,
        "property_count": len(binary_properties),
        "property_order_identical": binary_properties == ascii_properties,
        "mismatched_rows": mismatched_rows,
        "mismatched_values": mismatched_values,
        "binary_trailing_data": binary_trailing,
        "ascii_trailing_data": ascii_trailing,
    }
    result["exact_float32_conversion"] = (
        mismatched_values == 0 and not binary_trailing and not ascii_trailing
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("ascii", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.binary, args.ascii)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)
    raise SystemExit(0 if result["exact_float32_conversion"] else 1)


if __name__ == "__main__":
    main()
