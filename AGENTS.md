# AGENTS.md

## Scope

These instructions apply to the entire repository unless a more specific
`AGENTS.md` exists in a subdirectory.

## Collaboration rules

- Preserve existing tracked and untracked work. Check `git status --short`
  before editing and avoid unrelated cleanup.
- Do not create, modify, rename, or delete files beyond the user's requested
  scope.
- Briefly explain commands that write files, build the project, or run
  experiments before running them.
- Never run destructive commands or overwrite source fixtures, experiment
  results, or user data.
- Do not install dependencies, initialize submodules, or access external
  services without explicit approval.
- When uncertain, inspect the repository instead of guessing.
- Keep explanations approachable while retaining important technical details.
- Never place secrets, credentials, large datasets, model weights, generated
  builds, or machine-specific data in documentation or notes.

## Repository purpose

This repository is a fork of Google Draco adapted to encode and decode 3D
Gaussian Splatting (3DGS) point clouds. In addition to standard geometry
attributes, the fork supports 3DGS attributes such as spherical-harmonic color,
opacity, scale, and rotation.

The main workflow is:

```text
3DGS PLY input
  -> conversion to the supported ASCII PLY representation
  -> Draco point-cloud encoder
  -> .drc bitstream
  -> Draco decoder
  -> reconstructed PLY
  -> attribute-aware comparison or rendering
```

This fork is primarily intended for 3DGS experiments. Do not assume every
upstream Draco mesh, glTF, JavaScript, Unity, or Maya workflow has been kept in
sync with the custom attribute changes.

## Repository map

- `src/draco/tools/`: native command-line entry points, especially
  `draco_encoder.cc` and `draco_decoder.cc`.
- `src/draco/attributes/`: standard and custom geometry-attribute definitions.
- `src/draco/compression/`: codec APIs and point-cloud compression algorithms.
- `src/draco/io/`: PLY and other geometry readers and writers.
- `mytool/`: utilities for preparing and inspecting 3DGS PLY files.
- `myScript/`: experiment orchestration, encoding, decoding, and result scripts.
- `myJson/`: experiment configuration templates.
- `experiment_results/`: experiment-specific scripts and results. Preserve
  existing results; do not treat them as disposable build output.
- `testdata/3DGS/`: 3DGS test inputs. Never overwrite fixtures during a test.
- `testdata/`: upstream Draco fixtures and golden files.
- `submodules/3DGS-Interface/`: optional GS-Interface submodule used for 3DGS
  inspection or conversion.
- `javascript/`, `unity/`, and `maya/`: inherited platform integrations.
- `docs/`: Draco documentation and bitstream specification.
- `notes/`: repository learning notes and research questions.
- `README_original.md`: upstream/original documentation retained for reference.

## Native build

Keep builds out of the source tree. The README uses `build_dir/`:

```bash
cmake -S . -B build_dir -DCMAKE_BUILD_TYPE=Release
cmake --build build_dir -j2
```

Expected tools:

```text
build_dir/draco_encoder
build_dir/draco_decoder
```

Other local directories beginning with `build-` may contain experiment-specific
configurations. Do not delete, reconfigure, or reuse them without first checking
their purpose. Do not build merely to answer a read-only question.

## 3DGS conversion and encoding

Convert a 3DGS PLY to the representation expected by this fork:

```bash
python ./mytool/3DGS_pcd_to_draco_pcd.py \
  -i INPUT.ply \
  -o /tmp/OUTPUT_3dgs.ply
```

Encode and decode with temporary outputs:

```bash
./build_dir/draco_encoder -point_cloud \
  -i /tmp/OUTPUT_3dgs.ply \
  -o /tmp/OUTPUT_3dgs.drc

./build_dir/draco_decoder \
  -i /tmp/OUTPUT_3dgs.drc \
  -o /tmp/OUTPUT_3dgs_decoded.ply
```

Use `/tmp` or another user-approved output directory. Never overwrite the input
PLY or a file under `testdata/`.

## Custom 3DGS attributes and flags

The custom named attributes include:

- `F_DC`: base spherical-harmonic color.
- `F_REST_1`, `F_REST_2`, and `F_REST_3`: higher-order spherical-harmonic
  coefficients.
- `OPACITY`: Gaussian opacity.
- `SCALE`: Gaussian scale.
- `ROT`: Gaussian rotation.

Encoder quantization flags include `-qfd`, `-qfr1`, `-qfr2`, `-qfr3`, `-qo`,
`-qs`, and `-qr`. A quantization value of `0` disables quantization for that
attribute; it does not omit the attribute.

`--skip NORMAL`, `--skip SCALE`, and `--skip ROT` delete those attributes before
encoding. After decoding, an intentionally skipped attribute must be absent.
Treat omission and lossless retention as different experiment conditions.

When changing the attribute enum, serialization, encoder, or decoder, inspect
all relevant native and JavaScript mappings. Custom enum ordering can affect
bitstream compatibility, so do not reorder or renumber attributes casually.

## Tests and validation

Upstream native tests use GoogleTest and are disabled by default:

```bash
cmake -S . -B build-tests -DCMAKE_BUILD_TYPE=Release -DDRACO_TESTS=ON
cmake --build build-tests -j2
./build-tests/draco_tests
```

Do not initialize missing test dependencies or create a new test build without
user approval. Prefer the smallest validation appropriate to the change.

For 3DGS encoder or decoder changes, validate an encode/decode round trip using
a small fixture and check:

- the command exits successfully;
- point count and point order, when the experiment requires order preservation;
- attribute names, component counts, data types, and values;
- skipped attributes are absent;
- lossless attributes match exactly at the numeric-data level;
- quantized attributes stay within the expected tolerance;
- decoded output can be consumed by the intended renderer or interface.

Do not rely only on byte-for-byte `diff` for PLY files. Headers, formatting, and
serialization may differ even when the parsed data is equivalent. Use an
attribute-aware comparison script where possible, and record the comparison
criteria.

## External dependencies

Inspect optional dependencies with:

```bash
git submodule status
```

A leading `-` means a submodule is not initialized. In particular,
`submodules/3DGS-Interface` may be unavailable in a fresh checkout. Do not run
`git submodule update --init` without explicit approval because it writes files
and accesses an external repository.

Other optional toolchains include Emscripten, the Android NDK, Apple/Xcode,
Unity, and Maya. Do not assume they are installed.

## Code style

- Follow the Google C++ Style Guide as required by `CONTRIBUTING.md`.
- `.clang-format` is based on Google style with right-aligned pointers.
- Preserve existing copyright and Apache 2.0 headers.
- Match nearby naming, ownership, and error-handling patterns.
- Prefer `Status` and `StatusOr<T>` where surrounding Draco code uses them.
- Avoid unrelated formatting or cleanup in focused changes.
- Source files and targets are explicitly listed in CMake; update the correct
  lists when adding files.
- Search for `//! [YC]` when tracing fork-specific changes, but verify behavior
  from the implementation rather than assuming every marker is current.

## Generated and local files

- `build_dir/`, `build_C/`, and directories beginning with `build-` are generated
  build trees.
- `run-output/`, `output/`, `myresult/`, and similar paths are generated or local
  experiment output unless explicitly documented otherwise.
- `myData/`, `guassianData/`, and `expData/` may contain large local datasets.
- `docs/_site/` is generated documentation.
- Do not commit generated binaries, `.drc` outputs, decoded models, large PLY
  files, renders, or machine-specific paths unless the user explicitly asks.
- Do not inspect generated build trees as authoritative source unless diagnosing
  a particular build.

## Documentation and reporting

- Update `README.md` when user-facing commands, supported flags, attributes, or
  workflows change.
- Preserve `README_original.md` as the upstream reference unless explicitly
  asked to update it.
- Keep research notes distinct from confirmed behavior.
- Report exactly which commands and tests ran, what passed or failed, and what
  was not validated.
- Mention pre-existing working-tree changes separately from changes made during
  the current task.
