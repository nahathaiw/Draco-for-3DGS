# Experiment 3: Selective 3DGS quantization

Date executed: 2026-07-28

## Result

PASS. With 16-bit quantization applied only to SH/color attributes, every
position, normal, opacity, scale, and rotation value survived the round trip
bit-for-bit. The property layout, Gaussian count, and row ordering were also
preserved.

This is not a completely lossless round trip. It is lossless for geometry and
Gaussian shape parameters, with lossy 16-bit SH/color compression.

## Why we performed this experiment

A 3D Gaussian Splatting model contains two broad kinds of information:

1. **Geometry and Gaussian shape information** determines where every
   Gaussian is located and how it contributes to the scene.
2. **SH/color information** determines its color, including how that color
   changes with viewing direction.

Quantizing every attribute can reduce the file size, but it can also move the
Gaussians, change their transparency, distort their shape, or change their
orientation. If the rendered result changes, it is then difficult to tell
whether the cause was geometry, Gaussian shape, or color.

This experiment isolates color compression. It disables quantization for
geometry and Gaussian shape attributes while keeping quantization enabled for
SH/color attributes. The experiment answers these questions:

- Can Draco compress SH/color while preserving all non-color values exactly?
- Does the encoder preserve the Gaussian count and row ordering?
- How large are the numerical SH errors caused by 16-bit quantization?
- How much smaller is the compressed DRC?
- Can the base color, `f_dc`, be preserved while quantizing only the
  view-dependent higher-order SH coefficients?

This isolation is important scientifically. If position, opacity, scale, and
rotation are unchanged, differences in a later rendering can be attributed to
SH/color quantization instead of a mixture of unrelated changes.

## What “quantization” and the bit values mean

Quantization replaces floating-point values with values from a limited set of
levels. A smaller bit count normally provides fewer levels and more
compression, but introduces more numerical error. A larger bit count provides
more levels and normally reduces the error, but usually produces a larger
compressed file.

In this Draco-for-3DGS command-line implementation:

- A value greater than zero, such as `16`, enables quantization using that
  number of bits.
- A value of `0` disables the quantization transform for that attribute.
- Therefore, `0` means **no quantization**, not “store the attribute using
  zero bits.”

With quantization disabled, Draco still encodes and compresses the attribute;
it simply does not reduce its float precision through quantization. The
round-trip comparison is still necessary to prove that the implementation
actually preserves the original float32 bits.

## Meaning of the 3DGS attributes

Each row of the input PLY describes one Gaussian. This model has 136,641 rows.

| Attribute | Meaning | Why an error matters |
|---|---|---|
| `x`, `y`, `z` | Center position of the Gaussian in 3D space | An error moves the Gaussian and can alter geometry, edges, and alignment. |
| `nx`, `ny`, `nz` | Normal fields present in the PLY | They are non-color data, so this experiment preserves them. Standard 3DGS renderers may not use them directly. |
| `f_dc_0..2` | Degree-0 SH coefficients, one for each color channel | They represent the view-independent/base color contribution. Errors can change the general color from every view. |
| `f_rest_0..44` | Higher-order SH coefficients through degree 3 | They represent view-dependent color variation. Errors can change highlights and color as the camera moves. |
| `opacity` | Stored opacity parameter of the Gaussian | An error changes how strongly the Gaussian contributes and may make areas more transparent or opaque. |
| `scale_0..2` | Gaussian scale along its three local axes | An error changes the size and shape of the Gaussian. |
| `rot_0..3` | Quaternion-like rotation parameters | An error changes the Gaussian's orientation. |

The stored `opacity`, scale, and rotation values may be internal parameters
that a renderer transforms before use. This experiment compares the stored
float32 values directly, before any renderer-specific activation functions.

## Meaning of the command-line flags

| Flag | Controlled data | Setting in requested run | Meaning |
|---|---|---:|---|
| `-point_cloud` | Input geometry mode | enabled | Encodes the PLY as a point cloud/3DGS sequence rather than a triangle mesh. |
| `-i` | Input path | `3dgs.ply` | Selects the original model. |
| `-o` | Output path | `selective_sh16.drc` | Selects the compressed Draco file. |
| `-qp` | Position (`x`, `y`, `z`) | 0 | No position quantization. |
| `-qn` | Normals (`nx`, `ny`, `nz`) | 0 | No normal quantization. |
| `-qfd` | Degree-0 SH (`f_dc_0..2`) | 16 | Quantize base color to 16 bits. |
| `-qfr1` | Degree-1 `f_rest` group | 16 | Quantize the first higher-order SH group to 16 bits. |
| `-qfr2` | Degree-2 `f_rest` group | 16 | Quantize the second higher-order SH group to 16 bits. |
| `-qfr3` | Degree-3 `f_rest` group | 16 | Quantize the third higher-order SH group to 16 bits. |
| `-qo` | Opacity | 0 | No opacity quantization. |
| `-qs` | Scale | 0 | No scale quantization. |
| `-qr` | Rotation | 0 | No rotation quantization. |
| `-cl` | Compression level | 7 | Controls the encoder's compression effort/speed setting; it is separate from attribute precision. |

`qfr1`, `qfr2`, and `qfr3` are separate because degree-1, degree-2, and
degree-3 SH coefficients are stored as separate Draco attribute groups in this
fork. Together, the 45 `f_rest` properties contain 9 degree-1 values, 15
degree-2 values, and 21 degree-3 values.

## Why the settings had to change

The encoder defaults in this fork use 16-bit quantization for position,
normals, `f_dc`, all `f_rest` groups, opacity, scale, and rotation. Leaving the
defaults unchanged would make all those groups lossy.

For selective SH quantization, the non-color defaults therefore had to change
from `16` to `0`:

```text
qp: 16 -> 0    position becomes non-quantized
qn: 16 -> 0    normals become non-quantized
qo: 16 -> 0    opacity becomes non-quantized
qs: 16 -> 0    scale becomes non-quantized
qr: 16 -> 0    rotation becomes non-quantized
```

The SH settings stayed at 16:

```text
qfd:  16    quantized base color
qfr1: 16    quantized degree-1 SH
qfr2: 16    quantized degree-2 SH
qfr3: 16    quantized degree-3 SH
```

We also tested `qfd: 16 -> 0` separately. That companion run determines
whether preserving exact base color is practical while still compressing only
the higher-order, view-dependent color terms.

## Input and settings

- Input: `testdata/3DGS/3dgs.ply`
- Input format: binary little-endian PLY
- Gaussians: 136,641
- Properties: 62 float32 values per Gaussian
- Compression level: 7
- Non-color quantization: `qp=0`, `qn=0`, `qo=0`, `qs=0`, `qr=0`
- SH quantization: `qfd=16`, `qfr1=16`, `qfr2=16`, `qfr3=16`

Normals (`qn`) were also explicitly set to zero because they are non-color
attributes, even though they were omitted from the short experiment
description.

## Complete terminal walkthrough

The experiment input was not generated by GS-Interface. It is the 3DGS test
model tracked by the Draco-for-3DGS repository at
`testdata/3DGS/3dgs.ply`.

The commands below start from obtaining the repository and input. If the
repository is already available at `$REPO`,
skip the clone command and begin with `cd`.

### 1. Obtain the repository and input model

```bash
cd $WORKSPACE

# Only needed on a new machine. The tracked input PLY is included in this clone.
git clone https://github.com/SYJINTW/Draco-for-3DGS.git

cd $REPO

# Confirm that the input is a tracked repository file.
git ls-files testdata/3DGS/3dgs.ply

# Confirm its size and checksum.
stat -c '%n %s bytes' testdata/3DGS/3dgs.ply
sha256sum testdata/3DGS/3dgs.ply
```

Expected input verification:

```text
testdata/3DGS/3dgs.ply 33888499 bytes
be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c
```

The exact tracked input used in this workspace originated from repository
commit `c879605ede3ae43832f3cdb83da8cba01b3fbe22`.

### 2. Inspect the input PLY header

Do not use plain `head` on this binary PLY because it will print binary vertex
data after the header. This command stops at `end_header`:

```bash
sed -n '1,/end_header/p' testdata/3DGS/3dgs.ply
```

The important header fields are:

```text
format binary_little_endian 1.0
element vertex 136641
property float x
property float y
property float z
...
property float f_dc_0
property float f_dc_1
property float f_dc_2
...
property float f_rest_44
property float opacity
property float scale_0
property float scale_1
property float scale_2
property float rot_0
property float rot_1
property float rot_2
property float rot_3
end_header
```

### 3. Build the encoder and decoder

These commands are only required if `build-local/draco_encoder-1.5.6` and
`build-local/draco_decoder-1.5.6` do not already exist:

```bash
cd $REPO
cmake -S . -B build-local
cmake --build build-local --parallel

ls -lh \
  build-local/draco_encoder-1.5.6 \
  build-local/draco_decoder-1.5.6
```

### 4. Create the experiment directory

```bash
cd $REPO
mkdir -p experiment_results/7-28-26exp/exp3_selective_sh16
```

The comparison program used below is stored at:

```text
experiment_results/7-28-26exp/exp3_selective_sh16/compare_ply.py
```

It uses only the Python standard library. No NumPy, `plyfile`, or GS-Interface
installation is required. Its complete source can be shown in the terminal
with:

```bash
sed -n '1,260p' \
  experiment_results/7-28-26exp/exp3_selective_sh16/compare_ply.py
```

### 5. Requested run: quantize all SH/color groups to 16 bits

Encode:

```bash
cd $REPO

./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i testdata/3DGS/3dgs.ply \
  -o experiment_results/7-28-26exp/exp3_selective_sh16/selective_sh16.drc \
  -qp 0 -qn 0 \
  -qfd 16 -qfr1 16 -qfr2 16 -qfr3 16 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7
```

Decode:

```bash
./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp3_selective_sh16/selective_sh16.drc \
  -o experiment_results/7-28-26exp/exp3_selective_sh16/decoded_selective_sh16.ply
```

Compare every property at every original row:

```bash
python3 experiment_results/7-28-26exp/exp3_selective_sh16/compare_ply.py \
  testdata/3DGS/3dgs.ply \
  experiment_results/7-28-26exp/exp3_selective_sh16/decoded_selective_sh16.ply \
  --output experiment_results/7-28-26exp/exp3_selective_sh16/comparison.json
```

Show sizes and SHA-256 checksums:

```bash
stat -c '%n %s bytes' \
  testdata/3DGS/3dgs.ply \
  experiment_results/7-28-26exp/exp3_selective_sh16/selective_sh16.drc \
  experiment_results/7-28-26exp/exp3_selective_sh16/decoded_selective_sh16.ply

sha256sum \
  testdata/3DGS/3dgs.ply \
  experiment_results/7-28-26exp/exp3_selective_sh16/selective_sh16.drc \
  experiment_results/7-28-26exp/exp3_selective_sh16/decoded_selective_sh16.ply
```

### 6. Companion run: keep `f_dc` lossless

This run changes only `qfd` from 16 to 0. Higher-order `f_rest` groups remain
quantized to 16 bits.

```bash
cd $REPO

./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i testdata/3DGS/3dgs.ply \
  -o experiment_results/7-28-26exp/exp3_selective_sh16/selective_fdc0_rest16.drc \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 16 -qfr2 16 -qfr3 16 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7

./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/7-28-26exp/exp3_selective_sh16/selective_fdc0_rest16.drc \
  -o experiment_results/7-28-26exp/exp3_selective_sh16/decoded_fdc0_rest16.ply

python3 experiment_results/7-28-26exp/exp3_selective_sh16/compare_ply.py \
  testdata/3DGS/3dgs.ply \
  experiment_results/7-28-26exp/exp3_selective_sh16/decoded_fdc0_rest16.ply \
  --output experiment_results/7-28-26exp/exp3_selective_sh16/comparison_fdc0_rest16.json

stat -c '%n %s bytes' \
  experiment_results/7-28-26exp/exp3_selective_sh16/selective_fdc0_rest16.drc \
  experiment_results/7-28-26exp/exp3_selective_sh16/decoded_fdc0_rest16.ply

sha256sum \
  experiment_results/7-28-26exp/exp3_selective_sh16/selective_fdc0_rest16.drc \
  experiment_results/7-28-26exp/exp3_selective_sh16/decoded_fdc0_rest16.ply
```

### 7. Display the saved results

```bash
cd $REPO

sed -n '1,260p' \
  experiment_results/7-28-26exp/exp3_selective_sh16/REPORT.md

python3 -m json.tool \
  experiment_results/7-28-26exp/exp3_selective_sh16/comparison.json

python3 -m json.tool \
  experiment_results/7-28-26exp/exp3_selective_sh16/comparison_fdc0_rest16.json
```

## File sizes

| File | Bytes | Relative to original |
|---|---:|---:|
| Original PLY | 33,888,499 | 100.00% |
| Compressed DRC | 19,522,444 | 57.61% |
| Decoded PLY | 33,888,499 | 100.00% |

The DRC is 42.39% smaller than the original binary PLY. This ratio is recorded
for this dataset only.

## Attribute comparison

The comparison is index-preserving: each decoded row is compared directly
with the original row. Exact means identical float32 bits.

| Group | Values | Changed | Maximum absolute error | MAE | RMSE | Exact |
|---|---:|---:|---:|---:|---:|:---:|
| Position | 409,923 | 0 | 0 | 0 | 0 | Yes |
| Normal | 409,923 | 0 | 0 | 0 | 0 | Yes |
| Opacity | 136,641 | 0 | 0 | 0 | 0 | Yes |
| Scale | 409,923 | 0 | 0 | 0 | 0 | Yes |
| Rotation | 546,564 | 0 | 0 | 0 | 0 | Yes |
| `f_dc` | 409,923 | 409,760 | 9.393692e-05 | 4.690260e-05 | 5.413475e-05 | No |
| `f_rest_1` | 1,229,769 | 1,229,469 | 1.937151e-05 | 9.664873e-06 | 1.115728e-05 | No |
| `f_rest_2` | 2,049,615 | 2,049,091 | 1.543760e-05 | 7.645822e-06 | 8.831390e-06 | No |
| `f_rest_3` | 2,869,461 | 2,868,920 | 1.788139e-05 | 8.866557e-06 | 1.023747e-05 | No |

## Gaussian count and ordering

- Original count: 136,641
- Decoded count: 136,641
- Property names and order identical: yes
- Rows with any position difference: 0
- Ordering preserved by index and exact position tuple: yes

Because positions are bit-exact at every row and the count and schema are
unchanged, the decoder did not reorder the Gaussian sequence.

## Should `f_dc` remain lossless?

The implementation has independent controls: `qfd` controls `f_dc`, while
`qfr1`, `qfr2`, and `qfr3` control the higher-order SH groups. Therefore
`f_dc` can remain lossless without disabling higher-order SH quantization.

A companion run used `qfd=0` and `qfr1=qfr2=qfr3=16`:

| Result | All SH at 16 bits | `f_dc` lossless, `f_rest` at 16 bits |
|---|---:|---:|
| DRC size | 19,522,444 bytes | 20,383,921 bytes |
| DRC relative to original | 57.61% | 60.15% |
| `f_dc` changed values | 409,760 | 0 |
| `f_dc` maximum absolute error | 9.393692e-05 | 0 |
| Higher-order SH errors | Present | Identical to all-SH run |
| Non-SH values exact | Yes | Yes |
| Count/order preserved | Yes | Yes |

Keeping `f_dc` lossless costs 861,477 bytes for this model (4.41% more than
the all-SH-quantized DRC). It is not technically required for selective color
compression, but it is the correct setting if the experiment's intended claim
is “lossless base color with only view-dependent/higher-order SH loss.”

## Rendered appearance

No rendered comparison was produced. The included GS-Interface repository
states that it does not render 3DGS models; it reads, modifies, and exports PLY
data. A defensible appearance comparison needs an external 3DGS renderer, the
same saved cameras, and matched output settings. Render the original and both
decoded PLY files with those identical cameras before drawing a visual or
image-metric conclusion.

## Artifacts

- `selective_sh16.drc`: requested all-SH 16-bit compressed model
- `decoded_selective_sh16.ply`: requested decoded model
- `comparison.json`: machine-readable requested-run comparison
- `selective_fdc0_rest16.drc`: companion model with lossless `f_dc`
- `decoded_fdc0_rest16.ply`: decoded companion model
- `comparison_fdc0_rest16.json`: machine-readable companion comparison
- `compare_ply.py`: dependency-free, index-preserving comparison script
