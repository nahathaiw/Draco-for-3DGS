# Reproduce the Hotdog Selective Lossless Experiment

This experiment keeps only position, spherical-harmonic color, and opacity. It
removes normal, scale, and rotation while keeping every retained float32 value
bit-identical.

## Requirements

- Linux or another environment with Bash
- CMake
- A C++ compiler
- Python 3 (standard library only)
- GNU `time` at `/usr/bin/time`
- The Hotdog source PLY at:

```text
testdata/3DGS/hotdog/checkpoint/point_cloud/iteration_30000/point_cloud.ply
```

No Python packages need to be installed.

## Run everything

From the repository root, execute:

```bash
bash experiment_results/8-18-26/hotdog_position_color_opacity/run_experiment.sh
```

The script will:

1. Configure and build the current encoder and decoder under
   `/tmp/draco-3dgs-8-18-build`.
2. Convert the binary Hotdog PLY to exact ASCII float32 text.
3. Verify that the ASCII conversion changes no float32 bits.
4. Encode and decode an all-attribute lossless baseline.
5. Confirm that the baseline is byte-identical to the source.
6. Encode with `--skip NORMAL --skip SCALE --skip ROT`.
7. Decode and verify the selective output.
8. Write timings, sizes, hashes, and JSON verification results.

To use a different temporary build directory:

```bash
BUILD_DIR=/tmp/my-draco-build \
bash experiment_results/8-18-26/hotdog_position_color_opacity/run_experiment.sh
```

## Selective encoder command

The important command executed by the runner is:

```bash
/tmp/draco-3dgs-8-18-build/draco_encoder \
  -point_cloud \
  -i experiment_results/8-18-26/hotdog_position_color_opacity/hotdog_ascii.ply \
  -o experiment_results/8-18-26/hotdog_position_color_opacity/hotdog_position_color_opacity.drc \
  -qp 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 \
  --skip NORMAL \
  --skip SCALE \
  --skip ROT \
  -cl 7
```

The zero quantization values make the retained attributes lossless. The three
`--skip` options delete the unwanted attributes before encoding.

## Expected result

The command should report:

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

Expected verification:

```text
Gaussians:                  148,783 -> 148,783
Properties:                 62 -> 52
Retained changed values:    0
Position changed rows:      0
Unexpected properties:      none
Selective verification:     passed
```

Expected selective bitstream size:

```text
30,946,917 bytes
```

Small timing differences are normal across machines.

## Output files

The most useful persistent evidence is:

- `REPORT.md`: method, results, interpretation, and limitations.
- `log.md`: complete command history and observed output.
- `timings.txt`: measured time and peak memory for every stage.
- `sizes.txt`: source, intermediate, bitstream, and decoded sizes.
- `SHA256SUMS.txt`: artifact hashes.
- `ascii_verification.json`: exact conversion evidence.
- `baseline_verification.json`: all-attribute lossless baseline evidence.
- `selective_verification.json`: retained-attribute and omission evidence.

Generated local artifacts include:

- `hotdog_ascii.ply`
- `hotdog_baseline_lossless.drc`
- `hotdog_baseline_decoded.ply`
- `hotdog_position_color_opacity.drc`
- `hotdog_position_color_opacity_decoded.ply`
- Raw `*.log` command output

The large generated files and raw logs are ignored by Git. Running the script
again overwrites only these experiment outputs; it never modifies the source
Hotdog PLY.

## Interpret “lossless” correctly

This is a selectively lossless experiment:

- Position is exact.
- All `f_dc` and `f_rest` color values are exact.
- Opacity is exact.
- Gaussian order is exact.
- Normal, scale, and rotation are intentionally absent.

Because scale and rotation are required to reconstruct ordinary Gaussian
covariances, the selective decoded PLY is not directly equivalent to the
original rendering asset. A renderer must provide replacement values before
normal rendering.
