# Experiment 1: Skip normal and scale

Date: 2026-07-29
Result: **PASS**

## Objective

Read the original 3DGS PLY, omit the temporary in-memory NORMAL and SCALE
attributes before encoding, decode the DRC, and verify that:

- `nx`, `ny`, and `nz` are absent;
- `scale_0`, `scale_1`, and `scale_2` are absent;
- position, SH/color, opacity, and rotation remain bit-exact;
- Gaussian count and row ordering remain unchanged; and
- the original PLY remains unchanged.

## Skip semantics

The source file is not edited:

```text
Original PLY (unchanged)
        |
        v
Read all attributes into a temporary PointCloud
        |
        v
--skip NORMAL --skip SCALE
        |
        v
Delete NORMAL and SCALE from the temporary PointCloud
        |
        v
Encode and decode the 56 retained properties
```

`DeleteNamedAttributes(...)` is reused to remove the two named Draco
attributes. The explicit 3DGS skip path does not call point-ID deduplication,
protecting Gaussian identity and ordering.

## Implementation

The encoder now accepts:

```text
--skip NORMAL
--skip SCALE
```

The options can be supplied together or independently. `--skip ROT` remains
supported. Help output lists:

```text
NORMAL, TEX_COORD, GENERIC, SCALE, ROT
```

An invalid attribute name still fails with a nonzero exit status.

The six omitted PLY properties map to two internal attributes:

| Draco attribute | PLY properties |
|---|---|
| `GeometryAttribute::NORMAL` | `nx`, `ny`, `nz` |
| `GeometryAttribute::SCALE` | `scale_0`, `scale_1`, `scale_2` |

## Build

```bash
cmake -S . -B build-exp-normal-scale
cmake --build build-exp-normal-scale --parallel
```

The build completed successfully.

## Baseline command

```bash
./build-exp-normal-scale/draco_encoder-1.5.6 \
  -point_cloud \
  -i testdata/3DGS/3dgs.ply \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_all_attributes.drc \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7

./build-exp-normal-scale/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_all_attributes.drc \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_decoded.ply
```

The baseline decoded PLY is byte-for-byte identical to the source PLY.

## Skip command

```bash
./build-exp-normal-scale/draco_encoder-1.5.6 \
  -point_cloud \
  --skip NORMAL \
  --skip SCALE \
  -i testdata/3DGS/3dgs.ply \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/without_normal_scale.drc \
  -qp 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qr 0 \
  -cl 7

./build-exp-normal-scale/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-29-26exp/exp1_skip_normal_scale/without_normal_scale.drc \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/decoded_without_normal_scale.ply
```

The encoder log explicitly reports:

```text
Normals: Skipped
Scale: Skipped
Rotation: No quantization
```

## Verification

```bash
python3 experiment_results/7-29-26exp/exp1_skip_normal_scale/verify_exp1.py \
  --source testdata/3DGS/3dgs.ply \
  --decoded experiment_results/7-29-26exp/exp1_skip_normal_scale/decoded_without_normal_scale.ply \
  --expect-missing nx \
  --expect-missing ny \
  --expect-missing nz \
  --expect-missing scale_0 \
  --expect-missing scale_1 \
  --expect-missing scale_2 \
  --output experiment_results/7-29-26exp/exp1_skip_normal_scale/skip_verification.json
```

## Results

| Check | Baseline | Skip NORMAL + SCALE |
|---|---:|---:|
| Gaussian count | 136,641 | 136,641 |
| Property count | 62 | 56 |
| `nx`, `ny`, `nz` | Present | Absent |
| `scale_0..2` | Present | Absent |
| Unexpected missing properties | 0 | 0 |
| Unexpected extra properties | 0 | 0 |
| Retained property order | Preserved | Preserved |
| Retained changed rows | 0 | 0 |
| Retained changed float32 values | 0 | 0 |
| Baseline/source byte equality | Yes | Not applicable by design |

### Retained groups

| Retained group | Values compared | Changed | Bit-exact |
|---|---:|---:|:---:|
| Position: `x`, `y`, `z` | 409,923 | 0 | Yes |
| Base SH/color: `f_dc_0..2` | 409,923 | 0 | Yes |
| Higher SH/color: `f_rest_0..44` | 6,148,845 | 0 | Yes |
| Opacity | 136,641 | 0 | Yes |
| Rotation: `rot_0..3` | 546,564 | 0 | Yes |

Zero changed retained values at the same row proves both value preservation
and Gaussian ordering preservation for this dataset.

## Size comparison

| Artifact | Bytes |
|---|---:|
| Original PLY | 33,888,499 |
| Baseline DRC | 33,887,039 |
| Baseline decoded PLY | 33,888,499 |
| DRC without normal and scale | 30,607,643 |
| Decoded PLY without normal and scale | 30,608,992 |

Removing the six float32 properties saved:

```text
DRC:         3,279,396 bytes (9.677434%)
Decoded PLY: 3,279,507 bytes (9.677345%)
```

The six properties contain 3,279,384 raw bytes. The small additional
difference comes from removed attribute and PLY-header metadata.

## Checksums

```text
Original and baseline decoded PLY:
be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c

Baseline DRC:
d45f68080edc1f13ebdef136a01ac9fef076b00347fc3f01b6e5a2f884f94b11

DRC without normal and scale:
ef589cfb4439f9aaf3bd95d26dceec128cd6070107204becd077235691719e44

Decoded PLY without normal and scale:
ded77c1ee57cf7ccf09f46eb42641be57f01c7f999d582706979af537705bdd6
```

## Conclusion

The explicit NORMAL and SCALE skip feature works as intended. The original
PLY remains unchanged, the encoded and decoded results omit only the six
requested properties, and every retained position, SH/color, opacity, and
rotation value remains bit-for-bit identical at the same Gaussian row.
