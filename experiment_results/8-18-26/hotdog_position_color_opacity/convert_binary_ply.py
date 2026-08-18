#!/usr/bin/env python3
"""Convert a float32 binary little-endian vertex-only PLY to ASCII."""

import argparse
import struct
from pathlib import Path


def read_header(stream):
    lines = []
    vertex_count = None
    properties = []
    in_vertex = False
    while True:
        raw_line = stream.readline()
        if not raw_line:
            raise ValueError("PLY header has no end_header")
        line = raw_line.decode("ascii").rstrip("\r\n")
        lines.append(line)
        fields = line.split()
        if fields[:2] == ["element", "vertex"]:
            vertex_count = int(fields[2])
            in_vertex = True
        elif fields[:1] == ["element"]:
            if int(fields[2]) != 0:
                raise ValueError(f"Unsupported non-vertex element: {line}")
            in_vertex = False
        elif in_vertex and fields[:2] == ["property", "float"]:
            properties.append(fields[2])
        elif in_vertex and fields[:1] == ["property"]:
            raise ValueError(f"Unsupported vertex property: {line}")
        if line == "end_header":
            break

    if "format binary_little_endian 1.0" not in lines:
        raise ValueError("Input must be binary_little_endian PLY 1.0")
    if vertex_count is None or not properties:
        raise ValueError("PLY is missing its vertex count or float properties")
    return lines, vertex_count, properties


def convert(source_path, output_path):
    with source_path.open("rb") as source:
        header, vertex_count, properties = read_header(source)
        output_header = [
            "format ascii 1.0" if line.startswith("format ") else line
            for line in header
        ]
        row = struct.Struct("<" + "f" * len(properties))

        with output_path.open("w", encoding="ascii", newline="\n") as output:
            output.write("\n".join(output_header) + "\n")
            for index in range(vertex_count):
                encoded = source.read(row.size)
                if len(encoded) != row.size:
                    raise ValueError(f"Truncated vertex record at row {index}")
                values = row.unpack(encoded)
                output.write(" ".join(format(value, ".9g") for value in values))
                output.write("\n")

        if source.read(1):
            raise ValueError("Unexpected data after the vertex records")

    return vertex_count, len(properties)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    count, property_count = convert(args.source, args.output)
    print(f"Converted {count} vertices with {property_count} float properties")


if __name__ == "__main__":
    main()
