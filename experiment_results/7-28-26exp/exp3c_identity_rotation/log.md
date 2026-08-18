# Experiment 3C Log: Identity rotation with visible geometry preserved

Date: 2026-07-28
Status: **RUNNING**

## Objective

Keep position, normals, scale, SH/color, and opacity unchanged. Replace only
the four stored rotation properties with the common 3DGS identity quaternion:

```text
rot_0 = 1.0
rot_1 = 0.0
rot_2 = 0.0
rot_3 = 0.0
```

Then encode and decode without quantization and test whether Draco preserves
the modified PLY exactly.

Why:

Experiment 3B collapsed all positions to the origin and used an invalid
all-zero quaternion, so it was unsuitable for viewing in SuperSplat.
Experiment 3C preserves scene geometry and Gaussian sizes while using a valid
rotation. The rendered appearance may still change because every anisotropic
Gaussian loses its trained orientation.

## Workflow

```mermaid
flowchart LR
    A["Original PLY"] --> B["GS-Interface:<br/>set rotation to (1,0,0,0)"]
    B --> C["Verify all other values"]
    C --> D["Draco encode:<br/>all quantization off"]
    D --> E["Decode"]
    E --> F["Compare modified vs decoded"]
```

## Execution log

### Create guarded transformation and verification programs

Files:

```text
set_identity_rotation.py
verify_exp3c.py
```

Why:

The GS-Interface script explicitly changes only `rot_0..3`, refuses to
overwrite the source, exports a new PLY, reloads it, and verifies every
untargeted property. The independent verifier checks every float32 value by
row without using GS-Interface.

### Create the identity-rotation PLY

Terminal:

```bash
cd $GS_INTERFACE

.venv-exp3b/bin/python -m py_compile \
  ../Draco-for-3DGS/experiment_results/exp3c_identity_rotation/set_identity_rotation.py \
  ../Draco-for-3DGS/experiment_results/exp3c_identity_rotation/verify_exp3c.py

.venv-exp3b/bin/python \
  ../Draco-for-3DGS/experiment_results/exp3c_identity_rotation/set_identity_rotation.py \
  --input ../Draco-for-3DGS/testdata/3DGS/3dgs.ply \
  --output ../Draco-for-3DGS/experiment_results/exp3c_identity_rotation/identity_rotation.ply
```

Why:

Use GS-Interface to replace only the four rotation arrays with a valid identity
quaternion. Compile-check the programs before creating output.

Observed:

```text
Gaussians: 136,641
Properties: 62
Rotation: (1.0, 0.0, 0.0, 0.0)
Untargeted properties preserved: yes
Property order preserved: yes
Reload verification: passed
```

Result: **PASS**

### Lossless Draco encode and decode

Terminal:

```bash
cd $REPO

./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i experiment_results/exp3c_identity_rotation/identity_rotation.ply \
  -o experiment_results/exp3c_identity_rotation/identity_rotation_lossless.drc \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7

./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/exp3c_identity_rotation/identity_rotation_lossless.drc \
  -o experiment_results/exp3c_identity_rotation/decoded_identity_rotation.ply
```

Why:

Disable quantization for every attribute and test whether Draco preserves the
identity-rotation model without further loss.

Observed:

```text
All attribute groups: No quantization
Encode time: 54 ms
Encoded size: 33,887,039 bytes
Decoded Gaussians: 136,641
Decode time: 20 ms
```

Result: **PASS**

### Verify the round trip

Terminal:

```bash
cmp -s \
  experiment_results/exp3c_identity_rotation/identity_rotation.ply \
  experiment_results/exp3c_identity_rotation/decoded_identity_rotation.ply
echo $?

python3 experiment_results/exp3c_identity_rotation/verify_exp3c.py \
  --source testdata/3DGS/3dgs.ply \
  --modified experiment_results/exp3c_identity_rotation/identity_rotation.ply \
  --decoded experiment_results/exp3c_identity_rotation/decoded_identity_rotation.ply \
  --output experiment_results/exp3c_identity_rotation/roundtrip_verification.json

stat -c '%n %s bytes' \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3c_identity_rotation/identity_rotation.ply \
  experiment_results/exp3c_identity_rotation/identity_rotation_lossless.drc \
  experiment_results/exp3c_identity_rotation/decoded_identity_rotation.ply

sha256sum \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3c_identity_rotation/identity_rotation.ply \
  experiment_results/exp3c_identity_rotation/identity_rotation_lossless.drc \
  experiment_results/exp3c_identity_rotation/decoded_identity_rotation.ply
```

Why:

Combine byte-level equality, semantic property comparison, sizes, and
checksums.

Observed:

```text
cmp exit status: 0
Modified and decoded SHA-256:
316f593eeb047075b8d8d17f3700f09e08c440d9e6920564016527e5c3ac7b64
Headers identical: yes
Gaussian count and property order preserved: yes
Changed rows: 0
Changed float32 values: 0
```

Result: **PASS — byte-for-byte lossless**

## Final comparison

| Check | Original | Identity-rotation PLY | Decoded PLY |
|---|---|---|---|
| Position | Original | Bit-exact original | Bit-exact original |
| Scale | Original | Bit-exact original | Bit-exact original |
| SH/color | Original | Bit-exact original | Bit-exact original |
| Opacity | Original | Bit-exact original | Bit-exact original |
| Rotation | Trained values | `(1,0,0,0)` in every row | `(1,0,0,0)` in every row |
| Gaussians | 136,641 | 136,641 | 136,641 |
| PLY size | 33,888,499 | 33,888,499 | 33,888,499 |

| Compressed artifact | Size |
|---|---:|
| Identity-rotation lossless DRC | 33,887,039 bytes |

## Conclusion

Experiment 3C passed. GS-Interface changed only rotation to a valid identity
quaternion, and Draco preserved the entire modified model byte-for-byte.

`identity_rotation.ply` and `decoded_identity_rotation.ply` are ready for a
SuperSplat appearance check. The scene should no longer be collapsed because
position and scale are original. Its appearance may still differ because all
trained Gaussian orientations were intentionally removed.

Status: **COMPLETE**

### Independently verify the modification

Terminal:

```bash
cd $REPO

python3 experiment_results/exp3c_identity_rotation/verify_exp3c.py \
  --source testdata/3DGS/3dgs.ply \
  --modified experiment_results/exp3c_identity_rotation/identity_rotation.ply \
  --output experiment_results/exp3c_identity_rotation/modification_verification.json

stat -c '%n %s bytes' \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3c_identity_rotation/identity_rotation.ply

sha256sum \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3c_identity_rotation/identity_rotation.ply
```

Why:

Prove independently that only rotation changed and every Gaussian received the
exact identity quaternion.

Observed:

```text
All four rotation properties changed in all 136,641 rows.
Incorrect identity-rotation outputs: 0
Untargeted changed values: 0
Property order and Gaussian count preserved: yes
Modified size: 33,888,499 bytes
Modified SHA-256:
316f593eeb047075b8d8d17f3700f09e08c440d9e6920564016527e5c3ac7b64
```

Result: **PASS**
