# Experiment 3C: Identity rotation with geometry preserved

Date: 2026-07-28
Result: **PASS**

## Change

For every Gaussian:

```text
rot_0 = 1.0
rot_1 = 0.0
rot_2 = 0.0
rot_3 = 0.0
```

Position, normals, scale, SH/color, and opacity remained bit-exact.

## Motivation

Experiment 3B could not be viewed meaningfully because all positions were
moved to the origin and rotation became the invalid quaternion `(0,0,0,0)`.
Experiment 3C preserves the scene geometry and sizes while assigning the valid
identity quaternion `(1,0,0,0)`.

## Modification result

| Check | Result |
|---|---|
| Gaussians | 136,641 |
| Properties | 62 |
| All output rotations exactly `(1,0,0,0)` | Yes |
| Rotation values changed | 546,564 of 546,564 |
| Untargeted changed values | 0 |
| Property order preserved | Yes |

Modified PLY:

```text
experiment_results/7-28-26exp/exp3c_identity_rotation/identity_rotation.ply
Size: 33,888,499 bytes
SHA-256: 316f593eeb047075b8d8d17f3700f09e08c440d9e6920564016527e5c3ac7b64
```

## Lossless Draco result

All quantization options were set to zero. The encoder reported no
quantization for any attribute group.

| Artifact | Size |
|---|---:|
| Original PLY | 33,888,499 bytes |
| Identity-rotation PLY | 33,888,499 bytes |
| Lossless DRC | 33,887,039 bytes |
| Decoded identity-rotation PLY | 33,888,499 bytes |

The modified and decoded PLY files:

- have identical SHA-256 checksums;
- are byte-for-byte identical (`cmp` exit status 0);
- preserve 136,641 Gaussian rows;
- preserve property names and order;
- have zero changed float32 values.

## SuperSplat expectation

Use either of these files:

```text
identity_rotation.ply
decoded_identity_rotation.ply
```

They are identical. Unlike Experiment 3B, positions and scales remain
original, so the scene should be present. The visual result can still differ
from the original because anisotropic Gaussians no longer retain their trained
orientations. SuperSplat must be used to make the actual visual observation;
this repository does not provide that renderer.

## Artifacts

- `log.md`: commands, reasons, output, flowchart, and comparison
- `set_identity_rotation.py`: GS-Interface modification
- `verify_exp3c.py`: independent verification
- `identity_rotation.ply`: modified model for SuperSplat
- `identity_rotation_lossless.drc`: lossless compressed model
- `decoded_identity_rotation.ply`: lossless decoded model
- `modification_verification.json`: modification results
- `roundtrip_verification.json`: complete round-trip results
