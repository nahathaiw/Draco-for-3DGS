# Experiment 1: Lossless 3DGS round trip

Date executed: 2026-07-27

## Result

PASS for this dataset and encoder configuration.

- Every float32 property value was preserved bit-for-bit.
- The Gaussian count remained 136,641.
- All 62 property names, data types, and their layout were preserved.
- Gaussian row ordering was preserved.
- The decoded binary PLY was byte-for-byte identical to the valid original
  binary PLY.

This result demonstrates lossless round-trip behavior for this particular
input and command configuration. It does not prove that every possible PLY,
encoding method, or Draco configuration preserves values and ordering.

## Input integrity issue

The working-copy file at `testdata/3DGS/3dgs.ply` was not used because it was
corrupted. Its header declares a 33,886,968-byte vertex payload, but its actual
payload is 60,689,031 bytes and contains UTF-8 replacement-byte sequences.

The valid version from `HEAD:testdata/3DGS/3dgs.ply` was copied to
`original_binary.ply`. The corrupted working-copy file was not modified.

## Binary-to-ASCII conversion

The repository README states that the Draco input should be ASCII PLY. No PLY
Python dependencies were installed, so the fixed 62-float schema was converted
using Python's standard library. Each finite float32 was written with nine
significant decimal digits.

The conversion was verified by parsing the ASCII values back into float32 and
comparing their raw bytes with the binary input:

- Schema equal: yes
- Vertices: 136,641
- Properties: 62
- Mismatched rows: 0
- Non-finite input values: 0
- Undeclared trailing bytes: 0

## Encode command

```bash
./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp1_lossless/input_ascii.ply \
  -o experiment_results/7-28-26exp/exp1_lossless/roundtrip_q0.drc \
  -qp 0 \
  -qn 0 \
  -qfd 0 \
  -qfr1 0 \
  -qfr2 0 \
  -qfr3 0 \
  -qo 0 \
  -qs 0 \
  -qr 0 \
  -cl 7
```

The encoder log reported `No quantization` for positions, normals, `f_dc`,
all three `f_rest` groups, opacity, scale, and rotation.

## Decode command

```bash
./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp1_lossless/roundtrip_q0.drc \
  -o experiment_results/7-28-26exp/exp1_lossless/decoded_q0.ply
```

## Exact comparison

```bash
cmp -s \
  experiment_results/7-28-26exp/exp1_lossless/original_binary.ply \
  experiment_results/7-28-26exp/exp1_lossless/decoded_q0.ply
```

Exit status: `0` (identical).

Both PLY files are 33,888,499 bytes and have the same SHA-256:

```text
be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c
```

Since the complete decoded file is identical, all header bytes, property
layout bytes, vertex record bytes, and row positions are necessarily
identical. No GS-Interface investigation is needed for Experiment 1.

## Artifact sizes

```text
original_binary.ply   33,888,499 bytes
input_ascii.ply      105,076,099 bytes
roundtrip_q0.drc      33,887,039 bytes
decoded_q0.ply        33,888,499 bytes
```


original_binary.ply == original ply from Git(3dgs)
input_ascii.ply     == ASCII version according to dracofor 3dgs readme
roundtrip_q0.drc    == Droco-encoded file with quatization disable(losslelss)
decoded_q0.ply      == PLY reconstructed by draco
