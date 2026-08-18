# Experiment log: Skip NORMAL and SCALE

Date: 2026-07-29

## Requested task

Skip these properties during Draco encoding:

```text
nx
ny
nz
scale_0
scale_1
scale_2
```

Keep:

```text
x, y, z
f_dc_0..2
f_rest_0..44
opacity
rot_0..3
```

The source PLY must remain unchanged. NORMAL and SCALE are removed only from
the temporary in-memory point cloud before encoding.

## Initial code analysis

The earlier rotation experiment already added:

```cpp
DeleteNamedAttributes(...)
ApplyRotationSkip(...)
```

The PLY properties map to these internal Draco attributes:

```text
nx, ny, nz                -> GeometryAttribute::NORMAL
scale_0, scale_1, scale_2 -> GeometryAttribute::SCALE
```

Therefore, the implementation can remove two named Draco attributes instead
of editing six individual PLY properties.

The old `--skip NORMAL` path set normal quantization to `-1` and participated
in point-ID deduplication. For this 3DGS experiment, the explicit NORMAL and
SCALE skip path was separated from that legacy behavior so it does not
deduplicate or reorder Gaussians.

## Implementation

Modified:

```text
src/draco/tools/draco_encoder.cc
```

Added explicit option state:

```cpp
bool skip_normal;
bool skip_scale;
bool scale_deleted;
```

Added:

```cpp
ApplyNormalAndScaleSkip(...)
```

The helper reuses:

```cpp
DeleteNamedAttributes(point_cloud, GeometryAttribute::NORMAL);
DeleteNamedAttributes(point_cloud, GeometryAttribute::SCALE);
```

Extended `--skip` parsing and help output to support:

```bash
--skip NORMAL
--skip SCALE
```

Explicit 3DGS NORMAL skipping is excluded from point-ID deduplication.

## Build

Command:

```bash
cmake -S . -B build-exp-normal-scale
cmake --build build-exp-normal-scale --parallel
```

Result:

```text
Built target draco_encoder
Built target draco_decoder
```

## CLI validation

Help output:

```text
--skip ATTRIBUTE_NAME skip a given attribute
(NORMAL, TEX_COORD, GENERIC, SCALE, ROT)
```

Invalid test:

```bash
./build-exp-normal-scale/draco_encoder-1.5.6 \
  --skip BAD \
  -i testdata/3DGS/3dgs.ply \
  -o /tmp/invalid-skip.drc
```

Result:

```text
Error: Invalid attribute name after --skip
Exit status: 255
```

NORMAL-only and SCALE-only encoding were also tested independently:

```text
NORMAL-only: Normals: Skipped; Scale: No quantization
SCALE-only:  Normals: No quantization; Scale: Skipped
```

Both independent commands completed successfully.

## Baseline round trip

Encode:

```bash
./build-exp-normal-scale/draco_encoder-1.5.6 \
  -point_cloud \
  -i testdata/3DGS/3dgs.ply \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_all_attributes.drc \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7
```

Encoder output:

```text
Positions: No quantization
Normals: No quantization
f_dc: No quantization
f_rest_1: No quantization
f_rest_2: No quantization
f_rest_3: No quantization
Opacity: No quantization
Scale: No quantization
Rotation: No quantization
Encoded size = 33887039 bytes
```

Decode:

```bash
./build-exp-normal-scale/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_all_attributes.drc \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_decoded.ply
```

Decoder output:

```text
num_points: 136641
```

Exact comparison:

```bash
cmp -s \
  testdata/3DGS/3dgs.ply \
  experiment_results/7-29-26exp/exp1_skip_normal_scale/baseline_decoded.ply
```

Result:

```text
Exit status: 0
```

The baseline decoded PLY is byte-for-byte identical to the source.

## NORMAL and SCALE skip round trip

Encode:

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
```

Encoder output:

```text
Positions: No quantization
Normals: Skipped
f_dc: No quantization
f_rest_1: No quantization
f_rest_2: No quantization
f_rest_3: No quantization
Opacity: No quantization
Scale: Skipped
Rotation: No quantization
Encoded size = 30607643 bytes
```

Decode:

```bash
./build-exp-normal-scale/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-29-26exp/exp1_skip_normal_scale/without_normal_scale.drc \
  -o experiment_results/7-29-26exp/exp1_skip_normal_scale/decoded_without_normal_scale.ply
```

Decoder output:

```text
num_points: 136641
```

## Verification command

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

## Verification results

```text
Source Gaussian count:               136641
Decoded Gaussian count:              136641
Gaussian count preserved:            true
Source property count:               62
Decoded property count:              56
Missing properties match expected:   true
Unexpected extra properties:         none
Retained property order preserved:   true
Retained changed rows:               0
Retained changed float32 values:     0
All retained values bit-exact:       true
Unexpected trailing data:            false
```

Expected and actual missing properties:

```text
nx
ny
nz
scale_0
scale_1
scale_2
```

Retained group checks:

| Group | Values compared | Changed | Bit-exact |
|---|---:|---:|:---:|
| Position `x`, `y`, `z` | 409,923 | 0 | Yes |
| Base SH/color `f_dc_0..2` | 409,923 | 0 | Yes |
| Higher SH/color `f_rest_0..44` | 6,148,845 | 0 | Yes |
| Opacity | 136,641 | 0 | Yes |
| Rotation `rot_0..3` | 546,564 | 0 | Yes |

## Artifact sizes

| Artifact | Bytes |
|---|---:|
| Original PLY | 33,888,499 |
| Baseline DRC | 33,887,039 |
| Baseline decoded PLY | 33,888,499 |
| DRC without NORMAL and SCALE | 30,607,643 |
| Decoded PLY without NORMAL and SCALE | 30,608,992 |

Savings:

```text
DRC:         3,279,396 bytes (9.677434%)
Decoded PLY: 3,279,507 bytes (9.677345%)
```

## Checksums

```text
Original PLY:
be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c

Baseline DRC:
d45f68080edc1f13ebdef136a01ac9fef076b00347fc3f01b6e5a2f884f94b11

Baseline decoded PLY:
be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c

DRC without NORMAL and SCALE:
ef589cfb4439f9aaf3bd95d26dceec128cd6070107204becd077235691719e44

Decoded PLY without NORMAL and SCALE:
ded77c1ee57cf7ccf09f46eb42641be57f01c7f999d582706979af537705bdd6
```

## Conclusion

The experiment passed. NORMAL and SCALE are skipped from the encoded
representation without modifying the original PLY. The decoded result omits
only the six requested properties. Gaussian count and order remain unchanged,
and position, SH/color, opacity, and rotation remain bit-for-bit identical.
