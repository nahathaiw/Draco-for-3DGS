# Experiment 3B: Zero selected 3DGS attributes and losslessly round-trip

Date executed: 2026-07-28

## Purpose

Use GS-Interface to set selected geometry and Gaussian-shape property values
to numeric `0.0`, then test whether Draco-for-3DGS can encode and decode that
modified model without changing any additional information.

This experiment changes actual PLY data first. It then uses `0` for every
Draco quantization option, where `0` means **no quantization**.

## Result

**PASS.**

The modified encoder input and decoded output are byte-for-byte identical.
Their headers, 136,641 Gaussian rows, 62-property layout, property order, and
all 8,471,742 float32 values are identical.

## Input

```text
testdata/3DGS/3dgs.ply
Size: 33,888,499 bytes
SHA-256: be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c
Format: binary little-endian PLY
Gaussians: 136,641
Properties per Gaussian: 62 float32 values
```

## GS-Interface modification

The reproducible program is `zero_attributes.py`. It imports
`GaussianModelV2` from the sibling GS-Interface repository and assigns
float32 zero to:

```text
x, y, z
nx, ny, nz
scale_0, scale_1, scale_2
rot_0, rot_1, rot_2, rot_3
```

Command:

```bash
cd $GS_INTERFACE

.venv-exp3b/bin/python \
  ../Draco-for-3DGS/experiment_results/7-28-26exp/exp3b_zero_attributes/zero_attributes.py \
  --input ../Draco-for-3DGS/testdata/3DGS/3dgs.ply \
  --output ../Draco-for-3DGS/experiment_results/7-28-26exp/exp3b_zero_attributes/zeroed_attributes.ply
```

Independent verification found:

| Properties | Source state | Modified state | Result |
|---|---|---|---|
| `x`, `y`, `z` | 136,641 nonzero values each | All zero | Changed as requested |
| `nx`, `ny`, `nz` | Already all zero | All zero | Assignment made; bits unchanged |
| `scale_0..2` | 136,641 nonzero values each | All zero | Changed as requested |
| `rot_0..3` | 136,641 nonzero values each | All zero | Changed as requested |
| `f_dc_0..2` | Original values | Original values | Bit-exact |
| `f_rest_0..44` | Original values | Original values | Bit-exact |
| `opacity` | Original values | Original values | Bit-exact |

Untargeted changed values: **0**.

## Lossless encode and decode

Encode:

```bash
cd $REPO

./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp3b_zero_attributes/zeroed_attributes.ply \
  -o experiment_results/7-28-26exp/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7
```

The encoder reported `No quantization` for position, normals, `f_dc`, all
three `f_rest` groups, opacity, scale, and rotation.

Decode:

```bash
./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  -o experiment_results/7-28-26exp/exp3b_zero_attributes/decoded_zeroed_attributes.ply
```

## Round-trip verification

The correct lossless comparison is:

```text
zeroed_attributes.ply vs decoded_zeroed_attributes.ply
```

It is not decoded versus the original source because the GS-Interface change
was intentional.

```bash
cmp -s \
  experiment_results/7-28-26exp/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/7-28-26exp/exp3b_zero_attributes/decoded_zeroed_attributes.ply
echo $?
```

Observed `cmp` exit status: `0`.

Both PLY files have this SHA-256:

```text
8186f8afa6eac3a85a2b1fba29d7bca595d777b2c28b0ae96564ece35f114bc5
```

Property-aware verification:

| Check | Result |
|---|---|
| Gaussian count | 136,641 → 136,641 |
| Property count | 62 → 62 |
| Property order | Preserved |
| PLY header | Identical |
| Changed rows | 0 |
| Changed float32 values | 0 |
| Row/Gaussian ordering | Preserved |
| Byte-for-byte PLY equality | Yes |

## File sizes

| Artifact | Bytes |
|---|---:|
| Original source PLY | 33,888,499 |
| Modified zero-attribute PLY | 33,888,499 |
| Lossless DRC | 33,887,039 |
| Decoded PLY | 33,888,499 |

The DRC is 1,460 bytes smaller than the binary PLY, a reduction of only
0.004308%.

The earlier lossless DRC of the unmodified source is also exactly 33,887,039
bytes. The two DRC contents differ, but their sizes are equal. Therefore,
zeroing these properties did not improve the lossless compressed size in this
build and coding path.

## Conclusion

GS-Interface successfully produced the requested artificial model without
changing color, opacity, schema, count, or row order. Draco-for-3DGS then
preserved that complete modified model byte-for-byte when every quantization
option was disabled.

The lossless correctness hypothesis passed. The possible secondary hypothesis
that repeated zero values would reduce the DRC size did not: the modified and
unmodified lossless DRC files have exactly the same byte size.

## Reproducibility artifacts

- `log.md`: chronological commands, reasons, failures, corrections, and output
- `zero_attributes.py`: GS-Interface transformation program
- `verify_exp3b.py`: independent PLY verifier
- `zeroed_attributes.ply`: modified encoder input
- `zeroed_attributes_lossless.drc`: lossless Draco file
- `decoded_zeroed_attributes.ply`: decoded output
- `modification_verification.json`: source-to-modified verification
- `roundtrip_verification.json`: complete verification
