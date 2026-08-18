#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
BUILD_DIR=${BUILD_DIR:-/tmp/draco-3dgs-8-18-build}
SOURCE_PLY="$REPO_ROOT/testdata/3DGS/hotdog/checkpoint/point_cloud/iteration_30000/point_cloud.ply"
ASCII_PLY="$SCRIPT_DIR/hotdog_ascii.ply"
BASELINE_DRC="$SCRIPT_DIR/hotdog_baseline_lossless.drc"
BASELINE_PLY="$SCRIPT_DIR/hotdog_baseline_decoded.ply"
SELECTIVE_DRC="$SCRIPT_DIR/hotdog_position_color_opacity.drc"
SELECTIVE_PLY="$SCRIPT_DIR/hotdog_position_color_opacity_decoded.ply"
TIMINGS="$SCRIPT_DIR/timings.txt"

time_stage() {
  local stage=$1
  shift
  /usr/bin/time \
    -f "$stage\t%e\t%U\t%S\t%M" \
    -a -o "$TIMINGS" \
    "$@"
}

cd "$REPO_ROOT"
printf 'stage\twall_seconds\tuser_seconds\tsystem_seconds\tmax_rss_kb\n' > "$TIMINGS"

time_stage configure \
  cmake -S . -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DDRACO_TESTS=OFF \
    -DDRACO_TRANSCODER_SUPPORTED=OFF \
  2>&1 | tee "$SCRIPT_DIR/configure.log"

time_stage build \
  cmake --build "$BUILD_DIR" --target draco_encoder draco_decoder -j2 \
  2>&1 | tee "$SCRIPT_DIR/build.log"

time_stage convert_to_ascii \
  python3 "$SCRIPT_DIR/convert_binary_ply.py" "$SOURCE_PLY" "$ASCII_PLY" \
  2>&1 | tee "$SCRIPT_DIR/convert.log"

time_stage verify_ascii \
  python3 "$SCRIPT_DIR/verify_ascii_conversion.py" \
    "$SOURCE_PLY" "$ASCII_PLY" \
    --output "$SCRIPT_DIR/ascii_verification.json" \
  2>&1 | tee "$SCRIPT_DIR/verify-ascii.log"

time_stage baseline_encode \
  "$BUILD_DIR/draco_encoder" \
    -point_cloud \
    -i "$ASCII_PLY" \
    -o "$BASELINE_DRC" \
    -qp 0 -qn 0 \
    -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
    -qo 0 -qs 0 -qr 0 \
    -cl 7 \
  2>&1 | tee "$SCRIPT_DIR/baseline-encode.log"

time_stage baseline_decode \
  "$BUILD_DIR/draco_decoder" \
    -point_cloud \
    -i "$BASELINE_DRC" \
    -o "$BASELINE_PLY" \
  2>&1 | tee "$SCRIPT_DIR/baseline-decode.log"

time_stage baseline_verify \
  python3 "$SCRIPT_DIR/verify_roundtrip.py" \
    --source "$SOURCE_PLY" \
    --decoded "$BASELINE_PLY" \
    --output "$SCRIPT_DIR/baseline_verification.json" \
  2>&1 | tee "$SCRIPT_DIR/baseline-verify.log"

cmp "$SOURCE_PLY" "$BASELINE_PLY"

time_stage selective_encode \
  "$BUILD_DIR/draco_encoder" \
    -point_cloud \
    -i "$ASCII_PLY" \
    -o "$SELECTIVE_DRC" \
    -qp 0 \
    -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
    -qo 0 \
    --skip NORMAL \
    --skip SCALE \
    --skip ROT \
    -cl 7 \
  2>&1 | tee "$SCRIPT_DIR/selective-encode.log"

time_stage selective_decode \
  "$BUILD_DIR/draco_decoder" \
    -point_cloud \
    -i "$SELECTIVE_DRC" \
    -o "$SELECTIVE_PLY" \
  2>&1 | tee "$SCRIPT_DIR/selective-decode.log"

time_stage selective_verify \
  python3 "$SCRIPT_DIR/verify_roundtrip.py" \
    --source "$SOURCE_PLY" \
    --decoded "$SELECTIVE_PLY" \
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
    --output "$SCRIPT_DIR/selective_verification.json" \
  2>&1 | tee "$SCRIPT_DIR/selective-verify.log"

{
  printf 'source_ply\t%s\n' "$(stat -c %s "$SOURCE_PLY")"
  printf 'ascii_ply\t%s\n' "$(stat -c %s "$ASCII_PLY")"
  printf 'baseline_drc\t%s\n' "$(stat -c %s "$BASELINE_DRC")"
  printf 'baseline_decoded_ply\t%s\n' "$(stat -c %s "$BASELINE_PLY")"
  printf 'selective_drc\t%s\n' "$(stat -c %s "$SELECTIVE_DRC")"
  printf 'selective_decoded_ply\t%s\n' "$(stat -c %s "$SELECTIVE_PLY")"
} > "$SCRIPT_DIR/sizes.txt"

{
  sha256sum "$SOURCE_PLY" | sed "s|  $REPO_ROOT/|  |"
  sha256sum "$BASELINE_PLY" "$BASELINE_DRC" "$SELECTIVE_DRC" "$SELECTIVE_PLY" \
    | sed "s|  $SCRIPT_DIR/|  |"
} > "$SCRIPT_DIR/SHA256SUMS.txt"

git rev-parse HEAD > "$SCRIPT_DIR/source_commit.txt"

echo "Experiment passed."
cat "$TIMINGS"
cat "$SCRIPT_DIR/sizes.txt"
