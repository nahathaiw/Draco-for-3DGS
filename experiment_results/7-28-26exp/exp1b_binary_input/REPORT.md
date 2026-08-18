# Experiment 1B: Direct binary PLY input

Date executed: 2026-07-27

## Objective

Determine whether this `Draco-for-3DGS` build actually requires an ASCII PLY
input, as stated in the README, or whether it can consume the valid binary PLY
directly without changing values, layout, count, ordering, or encoded output.

## Result

PASS for this dataset and build.

- The encoder accepted the binary little-endian PLY directly.
- All relevant attributes reported `No quantization`.
- The decoded PLY was byte-for-byte identical to the original binary PLY.
- The DRC generated from binary input was byte-for-byte identical to the DRC
  previously generated from the verified ASCII input.

Therefore, ASCII conversion was not necessary for this dataset and executable.
This does not prove that every binary PLY variant is supported. Files with
different scalar types, list properties, elements, endianness, or schemas may
behave differently.

## Experimental comparison

Both experiments used 136,641 Gaussians, 62 `float32` properties, compression
level 7, and the same zero-quantization settings:

```text
-qp 0 -qn 0 -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 -qo 0 -qs 0 -qr 0
```

| Comparison | Experiment 1: ASCII input | Experiment 1B: Binary input |
|---|---:|---:|
| Encoder input size | 105,076,099 bytes | 33,888,499 bytes |
| Encoded DRC size | 33,887,039 bytes | 33,887,039 bytes |
| Decoded PLY size | 33,888,499 bytes | 33,888,499 bytes |
| Gaussian count preserved | Yes | Yes |
| 62-property layout preserved | Yes | Yes |
| Float32 values preserved bit-for-bit | Yes | Yes |
| Gaussian ordering preserved | Yes | Yes |
| Decoded PLY equals original binary PLY | Byte-for-byte identical | Byte-for-byte identical |
| DRC equals the other experiment's DRC | Yes | Yes |

The ASCII input is approximately 3.10 times larger than the binary input
because each float is stored as decimal text. This difference does not
represent additional 3DGS information. Both inputs produced the same DRC
bitstream and the same decoded PLY, so the input representation made no
difference to the encoded or reconstructed data in these experiments.

## Input

```text
experiment_results/7-28-26exp/exp1_lossless/original_binary.ply
```

The file is the valid version extracted from
`HEAD:testdata/3DGS/3dgs.ply`; the corrupted working-copy file was not used or
modified.

## Encode command

```bash
./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp1_lossless/original_binary.ply \
  -o experiment_results/7-28-26exp/exp1b_binary_input/binary_input_q0.drc \
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

The encoder reported no quantization for positions, normals, `f_dc`, all three
`f_rest` groups, opacity, scale, and rotation.

## Decode command

```bash
./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp1b_binary_input/binary_input_q0.drc \
  -o experiment_results/7-28-26exp/exp1b_binary_input/decoded_binary_input_q0.ply
```

The decoder reported 136,641 points.

## Comparisons

### Decoded binary-input PLY versus original PLY

`cmp` exit status: `0` (identical).

Both files are 33,888,499 bytes and share this SHA-256:

```text
be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c
```

This proves identical property layout, Gaussian count, float32 values, and
Gaussian ordering.

### Binary-input DRC versus ASCII-input DRC

`cmp` exit status: `0` (identical).

Both files are 33,887,039 bytes and share this SHA-256:

```text
d45f68080edc1f13ebdef136a01ac9fef076b00347fc3f01b6e5a2f884f94b11
```

The encoder therefore produced the same Draco bitstream from the verified
ASCII representation and the valid binary representation.

## Conclusion

For this standard 3DGS schema—136,641 vertices with 62 float32
properties—the tested `draco_encoder-1.5.6` executable supports direct binary
little-endian PLY input. The README's ASCII conversion instruction is more
restrictive than this observed behavior.
