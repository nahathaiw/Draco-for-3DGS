# Hotdog Position, Color, and Opacity Experiment Log

Date: 2026-08-18

This log records the command-line work used for the experiment. Paths are
written relative to `$REPO` so the commands work in another checkout.

```bash
export REPO=/path/to/Draco-for-3DGS
cd "$REPO"
export EXPERIMENT_DIR=experiment_results/8-18-26/hotdog_position_color_opacity
export SOURCE_PLY=testdata/3DGS/hotdog/checkpoint/point_cloud/iteration_30000/point_cloud.ply
export BUILD_DIR=/tmp/draco-3dgs-8-18-build
```

## 1. Repository and input preflight

The repository state and source revision were inspected first:

```bash
git status -sb
git log -2 --oneline --decorate
```

The branch was clean before the experiment. The tested source revision was:

```text
8e74e232005ebfd720dfc578e229a4faac36dd11
```

The input file was inspected without changing it:

```bash
stat -c 'path=%n\nsize_bytes=%s\nmodified=%y' "$SOURCE_PLY"
sha256sum "$SOURCE_PLY"
head -c 8192 "$SOURCE_PLY" | sed -n '1,/end_header/p'
```

Observed input:

```text
Size:       36,899,715 bytes
SHA-256:    6627c742839390c92d2e272295e3dbaa2b55b278c7b797f9451c3333a3f65fcd
Format:     binary_little_endian PLY 1.0
Gaussians:  148,783
Properties: 62 float32 values per Gaussian
```

Tool availability was checked with:

```bash
command -v cmake
command -v /usr/bin/time
python3 --version
c++ --version | sed -n '1p'
```

Observed versions:

```text
Python 3.14.4
GNU C++ 15.2.0
```

## 2. Script checks

The experiment scripts were checked before execution:

```bash
bash -n "$EXPERIMENT_DIR/run_experiment.sh"
python3 -m py_compile \
  "$EXPERIMENT_DIR/convert_binary_ply.py" \
  "$EXPERIMENT_DIR/verify_ascii_conversion.py" \
  "$EXPERIMENT_DIR/verify_roundtrip.py"
git diff --check
```

All checks passed.

## 3. Complete experiment command

The complete experiment was run with:

```bash
bash "$EXPERIMENT_DIR/run_experiment.sh"
```

The runner executed the following commands.

### Configure

```bash
cmake -S . -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DDRACO_TESTS=OFF \
  -DDRACO_TRANSCODER_SUPPORTED=OFF
```

CMake completed successfully. It emitted the known developer warning about
policy `CMP0148`; configuration still succeeded.

### Build

```bash
cmake --build "$BUILD_DIR" \
  --target draco_encoder draco_decoder \
  -j2
```

Both native tools built successfully.

### Convert the binary source to exact ASCII float32 text

```bash
python3 "$EXPERIMENT_DIR/convert_binary_ply.py" \
  "$SOURCE_PLY" \
  "$EXPERIMENT_DIR/hotdog_ascii.ply"
```

Output:

```text
Converted 148783 vertices with 62 float properties
```

### Verify the ASCII conversion

```bash
python3 "$EXPERIMENT_DIR/verify_ascii_conversion.py" \
  "$SOURCE_PLY" \
  "$EXPERIMENT_DIR/hotdog_ascii.ply" \
  --output "$EXPERIMENT_DIR/ascii_verification.json"
```

Result:

```text
Mismatched rows:   0
Mismatched values: 0
Exact float32 conversion: true
```

### Encode the all-attribute lossless baseline

```bash
"$BUILD_DIR/draco_encoder" \
  -point_cloud \
  -i "$EXPERIMENT_DIR/hotdog_ascii.ply" \
  -o "$EXPERIMENT_DIR/hotdog_baseline_lossless.drc" \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7
```

The encoder reported `No quantization` for every attribute. Its internal timer
reported 57 ms, and the bitstream size was 36,898,255 bytes.

### Decode and verify the baseline

```bash
"$BUILD_DIR/draco_decoder" \
  -point_cloud \
  -i "$EXPERIMENT_DIR/hotdog_baseline_lossless.drc" \
  -o "$EXPERIMENT_DIR/hotdog_baseline_decoded.ply"

python3 "$EXPERIMENT_DIR/verify_roundtrip.py" \
  --source "$SOURCE_PLY" \
  --decoded "$EXPERIMENT_DIR/hotdog_baseline_decoded.ply" \
  --output "$EXPERIMENT_DIR/baseline_verification.json"

cmp "$SOURCE_PLY" "$EXPERIMENT_DIR/hotdog_baseline_decoded.ply"
```

The decoder's internal timer reported 24 ms. Verification and `cmp` both
passed. The original and baseline-decoded files have the same SHA-256 digest.

### Encode only position, color, and opacity

```bash
"$BUILD_DIR/draco_encoder" \
  -point_cloud \
  -i "$EXPERIMENT_DIR/hotdog_ascii.ply" \
  -o "$EXPERIMENT_DIR/hotdog_position_color_opacity.drc" \
  -qp 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 \
  --skip NORMAL \
  --skip SCALE \
  --skip ROT \
  -cl 7
```

The encoder reported:

```text
Positions: No quantization
Normals: Skipped
f_dc: No quantization
f_rest_1: No quantization
f_rest_2: No quantization
f_rest_3: No quantization
Opacity: No quantization
Scale: Skipped
Rotation: Skipped
```

Its internal timer reported 35 ms. The selective bitstream was 30,946,917
bytes.

### Decode and verify the selective stream

```bash
"$BUILD_DIR/draco_decoder" \
  -point_cloud \
  -i "$EXPERIMENT_DIR/hotdog_position_color_opacity.drc" \
  -o "$EXPERIMENT_DIR/hotdog_position_color_opacity_decoded.ply"

python3 "$EXPERIMENT_DIR/verify_roundtrip.py" \
  --source "$SOURCE_PLY" \
  --decoded "$EXPERIMENT_DIR/hotdog_position_color_opacity_decoded.ply" \
  --expect-missing nx \
  --expect-missing ny \
  --expect-missing nz \
  --expect-missing scale_0 \
  --expect-missing scale_1 \
  --expect-missing scale_2 \
  --expect-missing rot_0 \
  --expect-missing rot_1 \
  --expect-missing rot_2 \
  --expect-missing rot_3 \
  --output "$EXPERIMENT_DIR/selective_verification.json"
```

The decoder's internal timer reported 20 ms. Verification passed.

## 4. Timing commands

Each runner stage was wrapped with GNU `time` in this form:

```bash
/usr/bin/time \
  -f 'STAGE_NAME\t%e\t%U\t%S\t%M' \
  -a -o "$EXPERIMENT_DIR/timings.txt" \
  COMMAND ARGUMENTS...
```

Measured results:

| Stage | Wall | User | System | Peak RSS |
|---|---:|---:|---:|---:|
| Configure | 0.45 s | 0.24 s | 0.21 s | 28,484 KiB |
| Build | 54.15 s | 91.80 s | 12.41 s | 312,048 KiB |
| Convert to ASCII | 2.07 s | 2.02 s | 0.04 s | 16,024 KiB |
| Verify ASCII | 2.22 s | 2.19 s | 0.02 s | 15,948 KiB |
| Baseline encode | 0.79 s | 0.62 s | 0.16 s | 188,876 KiB |
| Baseline decode | 0.12 s | 0.03 s | 0.08 s | 125,424 KiB |
| Baseline verification | 4.61 s | 4.58 s | 0.01 s | 22,656 KiB |
| Selective encode | 0.76 s | 0.62 s | 0.14 s | 188,808 KiB |
| Selective decode | 0.09 s | 0.03 s | 0.06 s | 106,196 KiB |
| Selective verification | 4.35 s | 4.32 s | 0.02 s | 23,068 KiB |

## 5. Size and checksum commands

The runner recorded sizes with `stat` and hashes with `sha256sum`:

```bash
stat -c %s "$SOURCE_PLY"
stat -c %s "$EXPERIMENT_DIR/hotdog_ascii.ply"
stat -c %s "$EXPERIMENT_DIR/hotdog_baseline_lossless.drc"
stat -c %s "$EXPERIMENT_DIR/hotdog_baseline_decoded.ply"
stat -c %s "$EXPERIMENT_DIR/hotdog_position_color_opacity.drc"
stat -c %s "$EXPERIMENT_DIR/hotdog_position_color_opacity_decoded.ply"

sha256sum "$SOURCE_PLY"
sha256sum "$EXPERIMENT_DIR/hotdog_baseline_decoded.ply"
sha256sum "$EXPERIMENT_DIR/hotdog_baseline_lossless.drc"
sha256sum "$EXPERIMENT_DIR/hotdog_position_color_opacity.drc"
sha256sum "$EXPERIMENT_DIR/hotdog_position_color_opacity_decoded.ply"
```

Results are stored in `sizes.txt` and `SHA256SUMS.txt`.

## 6. Portability cleanup and revalidation

After the initial successful run, the verification scripts were updated to
record repository-relative paths instead of the local machine's absolute path.
The shell script was also updated to write portable labels to the size and
checksum files. Script syntax was checked again, and these lightweight
verification commands were rerun:

```bash
bash -n "$EXPERIMENT_DIR/run_experiment.sh"
python3 -m py_compile \
  "$EXPERIMENT_DIR/verify_ascii_conversion.py" \
  "$EXPERIMENT_DIR/verify_roundtrip.py"

python3 "$EXPERIMENT_DIR/verify_ascii_conversion.py" \
  "$SOURCE_PLY" \
  "$EXPERIMENT_DIR/hotdog_ascii.ply" \
  --output "$EXPERIMENT_DIR/ascii_verification.json"

python3 "$EXPERIMENT_DIR/verify_roundtrip.py" \
  --source "$SOURCE_PLY" \
  --decoded "$EXPERIMENT_DIR/hotdog_baseline_decoded.ply" \
  --output "$EXPERIMENT_DIR/baseline_verification.json"

python3 "$EXPERIMENT_DIR/verify_roundtrip.py" \
  --source "$SOURCE_PLY" \
  --decoded "$EXPERIMENT_DIR/hotdog_position_color_opacity_decoded.ply" \
  --expect-missing nx --expect-missing ny --expect-missing nz \
  --expect-missing scale_0 --expect-missing scale_1 --expect-missing scale_2 \
  --expect-missing rot_0 --expect-missing rot_1 \
  --expect-missing rot_2 --expect-missing rot_3 \
  --output "$EXPERIMENT_DIR/selective_verification.json"
```

All three verification commands passed again.

## 7. Final result

- Exactly 10 properties were removed.
- Exactly 52 properties were retained.
- Gaussian count remained 148,783.
- Gaussian ordering was preserved.
- All 7,736,716 retained float32 values were bit-identical.
- The selective `.drc` was 5,951,338 bytes smaller than the full lossless
  baseline, a 16.129050% reduction.
- No source dataset file was modified.
