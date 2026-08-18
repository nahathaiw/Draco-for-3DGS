# Experiment 3B Learning Log: Zero selected attributes, then lossless round trip

Status: **PLANNING — experiment commands have not been executed**

This file is both a laboratory log and a step-by-step tutorial. During the
experiment, each command will be recorded here with:

- the exact terminal command;
- why we ran it;
- what we expected;
- what actually happened;
- the date and relevant output.

Creating this planning log does not modify the input model and does not start
the experiment.

## 1. Research question

Can we replace selected geometry and Gaussian-shape values in a 3DGS PLY with
numeric zero, then encode and decode that modified model with Draco without
losing or changing any additional information?

This is different from setting Draco quantization options to zero:

- **PLY value `0.0`** means we changed the stored model data itself.
- **Draco option `-q... 0`** means Draco must not apply quantization to that
  attribute group.

Experiment 3B intentionally does both, but at different stages.

## 2. Intended data changes

For every Gaussian, GS-Interface will set these stored float properties to
`0.0`:

```text
x, y, z
nx, ny, nz
scale_0, scale_1, scale_2
rot_0, rot_1, rot_2, rot_3
```

These properties must remain unchanged:

```text
f_dc_0, f_dc_1, f_dc_2
f_rest_0 through f_rest_44
opacity
```

The property names, property order, Gaussian count, and Gaussian row order
must also remain unchanged.

## 3. Files and comparison relationships

```text
testdata/3DGS/3dgs.ply
        |
        | GS-Interface: set selected property values to 0.0
        v
experiment_results/exp3b_zero_attributes/zeroed_attributes.ply
        |
        | Draco encode with every quantization option set to 0
        v
experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc
        |
        | Draco decode
        v
experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply
```

Two comparisons answer two different questions:

1. **Original vs modified PLY:** Did GS-Interface change only the requested
   properties?
2. **Modified vs decoded PLY:** Did Draco preserve the complete modified model
   losslessly?

The decoded file should not be compared to the original source as a lossless
test because we intentionally changed selected values before compression.

## 4. Planned workflow

### Step 0 — Enter the repository

Planned terminal command:

```bash
cd $REPO
pwd
```

Why:

All following paths are relative to the Draco-for-3DGS repository. Printing
the current directory prevents commands from accidentally targeting a
different repository.

Expected output:

```text
$REPO
```

Execution record: **not yet executed**

### Step 1 — Confirm the source input

Planned terminal commands:

```bash
git ls-files testdata/3DGS/3dgs.ply
stat -c '%n %s bytes' testdata/3DGS/3dgs.ply
sha256sum testdata/3DGS/3dgs.ply
sed -n '1,/end_header/p' testdata/3DGS/3dgs.ply
```

Why:

- `git ls-files` confirms that the input is a tracked repository file.
- `stat` records the original byte size.
- `sha256sum` gives the exact input a reproducible identity.
- `sed` displays only the PLY header so we can confirm the vertex count,
  binary format, property types, and property order without printing binary
  vertex data.

Expected facts from the current repository:

```text
Size: 33,888,499 bytes
SHA-256: be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c
Format: binary_little_endian 1.0
Vertices/Gaussians: 136,641
Vertex properties: 62 float32 properties
```

Execution record: **not yet executed for Experiment 3B**

### Step 2 — Confirm GS-Interface and its dependencies

Planned terminal commands:

```bash
cd $GS_INTERFACE
python3 --version
python3 -c "import numpy; import plyfile; print('GS-Interface dependencies available')"
```

Why:

`GS-Interface/io_3dgs.py` imports NumPy and `plyfile`. We must verify that the
same Python environment can import them before changing any model data.

If the dependency check fails, we will stop and record the failure. Installing
packages changes the environment and may require network access, so that step
will be discussed before it is performed.

Execution record: **not yet executed**

### Step 3 — Inspect the GS-Interface API before using it

Planned terminal commands:

```bash
cd $GS_INTERFACE
sed -n '1,180p' io_3dgs.py
```

Why:

We should understand the exact loading, attribute storage, and export behavior
before trusting it with the model. In particular, we will inspect:

- `GaussianModelV2.load_gaussian_ply()`;
- `GaussianModelV2.export_gs_to_ply()`;
- the `data[property_name]["data"]` arrays;
- whether property insertion order is preserved during export.

Execution record: **not yet executed for Experiment 3B**

### Step 4 — Create a small, explicit GS-Interface modification script

Planned file:

```text
experiment_results/exp3b_zero_attributes/zero_attributes.py
```

Planned behavior:

1. Load the original PLY with `GaussianModelV2`.
2. Check that every requested property exists.
3. Preserve the original property-name order.
4. Set only the 13 requested property arrays to numeric `0.0`.
5. Export a new binary PLY.
6. Reload the output using GS-Interface.
7. Confirm that all targeted values are zero.
8. Confirm that untargeted values, count, and schema remain unchanged.
9. Never overwrite `testdata/3DGS/3dgs.ply`.

Planned terminal command after reviewing the script:

```bash
cd $GS_INTERFACE
python3 \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zero_attributes.py \
  --input ../Draco-for-3DGS/testdata/3DGS/3dgs.ply \
  --output ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zeroed_attributes.ply
```

Why:

A dedicated script makes the transformation repeatable and auditable. Explicit
property names prevent a broad pattern from accidentally zeroing color,
opacity, or another attribute.

Execution record: **script not yet created; command not executed**

### Step 5 — Verify the modification independently

Planned checks:

```bash
cd $REPO

stat -c '%n %s bytes' \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply

sha256sum \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply

sed -n '1,/end_header/p' \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply
```

We will also use a comparison program to report, by property:

- total values;
- changed values;
- whether every targeted output value is exactly zero;
- whether every untargeted value is bit-identical;
- Gaussian counts;
- property names and property order.

Why:

Successfully writing a PLY is not enough. This verification proves that the
modification script changed exactly the intended data and nothing else.

Expected result:

- The 13 targeted properties are all `0.0`.
- The 49 untargeted properties are bit-exact.
- Both files contain 136,641 Gaussians.
- Both files contain the same 62 properties in the same order.
- Row order is preserved.

Execution record: **not yet executed**

### Step 6 — Confirm the Draco executables

Planned terminal commands:

```bash
cd $REPO
ls -lh \
  build-local/draco_encoder-1.5.6 \
  build-local/draco_decoder-1.5.6

./build-local/draco_encoder-1.5.6 -h
./build-local/draco_decoder-1.5.6 -h
```

Why:

This records which local programs perform the round trip and confirms that
they run before we begin encoding.

Execution record: **not yet executed for Experiment 3B**

### Step 7 — Losslessly encode the modified PLY

Planned terminal command:

```bash
cd $REPO

./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  -o experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  -qp 0 \
  -qn 0 \
  -qfd 0 \
  -qfr1 0 \
  -qfr2 0 \
  -qfr3 0 \
  -qo 0 \
  -qs 0 \
  -qr 0 \
  -cl 7
```

Why:

Every quantization option is set to `0`, which tells this fork not to apply a
quantization transform to any stored attribute group. This isolates the effect
of the earlier PLY modification from lossy Draco quantization.

Important:

`-qp 0` does not set positions to zero. The GS-Interface step already changed
the position values. Here, `-qp 0` only disables position quantization.

Expected encoder messages:

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
```

Execution record: **not yet executed**

### Step 8 — Decode the DRC

Planned terminal command:

```bash
cd $REPO

./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  -o experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply
```

Why:

The decompressed PLY is required to test whether Draco preserved the modified
model exactly.

Expected decoded count:

```text
136641
```

Execution record: **not yet executed**

### Step 9 — Compare modified input with decoded output

The primary lossless check will compare:

```text
zeroed_attributes.ply
decoded_zeroed_attributes.ply
```

Planned first check:

```bash
cd $REPO

cmp \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply

echo $?
```

Why:

`cmp` performs a byte-for-byte comparison:

- exit status `0` means the files are completely identical;
- exit status `1` means bytes differ;
- another status indicates an error.

If `cmp` reports a difference, that alone does not explain it. We will then
run a property-aware PLY comparison to determine whether the difference is
only file serialization or whether any actual values, schema, count, or order
changed.

Planned checksum and size commands:

```bash
stat -c '%n %s bytes' \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply

sha256sum \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply
```

Expected result:

- Modified and decoded Gaussian counts match.
- Property schema and order match.
- Every stored float32 value matches bit-for-bit.
- Gaussian row order matches.
- Ideally, the two PLY files are byte-for-byte identical.

Execution record: **not yet executed**

### Step 10 — Record and interpret file sizes

We will record:

```text
Original source PLY size
Modified zero-attribute PLY size
Compressed DRC size
Decoded PLY size
```

Why:

The original and modified binary PLY files will probably have the same size
because they contain the same number and type of float32 fields. The values
changed, but the fixed-width PLY representation did not.

The lossless DRC may be smaller when many selected values are identical zeros
because repeated or predictable data can be compressed efficiently. This is a
hypothesis to measure, not a result to assume.

Execution record: **not yet executed**

### Step 11 — Write the final report

Planned report:

```text
experiment_results/exp3b_zero_attributes/REPORT.md
```

It will contain:

- the purpose and hypothesis;
- exact input identity;
- GS-Interface modification code and command;
- verification that only selected properties changed;
- exact encoder and decoder commands;
- encoder and decoder output;
- original, modified, DRC, and decoded sizes;
- byte-level and property-level comparisons;
- Gaussian count and ordering results;
- limitations and conclusion.

Execution record: **not yet written**

## 5. Safety and validity rules

We will follow these rules:

1. Never modify or overwrite `testdata/3DGS/3dgs.ply`.
2. Write every generated file only inside
   `experiment_results/exp3b_zero_attributes/`.
3. Check required properties before setting any values.
4. Set properties by explicit name, not a broad wildcard.
5. Verify the GS-Interface output before giving it to Draco.
6. Use zero quantization for every Draco attribute group.
7. Compare the decoded output against the modified PLY.
8. Preserve and verify Gaussian row order.
9. Record failures and unexpected output instead of silently correcting them.
10. Distinguish measured results from expectations.

## 6. What this experiment will and will not prove

If the round trip passes, it will prove for this model and this Draco build
that the deliberately modified PLY can be encoded and decoded without further
attribute loss, count changes, or reordering.

It will not prove that:

- the modified model represents the original scene;
- the modified model renders correctly;
- every possible PLY schema is supported;
- every Draco version behaves identically;
- zero-valued rotation and scale are meaningful renderer inputs.

The experiment is primarily a data-transformation and lossless-round-trip
test, not a visual-quality test.

## 7. Detailed execution records

The records below were appended throughout the run. Use the chronological
index in Section 9 for the actual execution order.

### 2026-07-28 — Experiment started

Commands:

```bash
cd $REPO
pwd
git ls-files testdata/3DGS/3dgs.ply
stat -c '%n %s bytes' testdata/3DGS/3dgs.ply
sha256sum testdata/3DGS/3dgs.ply
git log -1 --format='%H %cs %s' -- testdata/3DGS/3dgs.ply
sed -n '1,/end_header/p' testdata/3DGS/3dgs.ply
ls -l build-local/draco_encoder-1.5.6 build-local/draco_decoder-1.5.6
```

Why:

Identify the exact tracked input, inspect its schema, and verify that the
previously built encoder and decoder exist before creating outputs.

Observed:

```text
Repository: $REPO
Tracked input: testdata/3DGS/3dgs.ply
Input size: 33,888,499 bytes
Input SHA-256: be1e690a9e9a2543a39f7181fec0062f088221b968acd617940ff96679661a4c
Input commit: c879605ede3ae43832f3cdb83da8cba01b3fbe22
Input format: binary_little_endian 1.0
Gaussian count: 136,641
Encoder and decoder: present and executable
```

Result: **PASS**

### 2026-07-28 — Decode the modified lossless DRC

Command:

```bash
cd $REPO

./build-local/draco_decoder-1.5.6 \
  -point_cloud \
  -i experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  -o experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply
```

Why:

Reconstruct a PLY that can be compared directly with the modified encoder
input.

Observed:

```text
Decoded Gaussian count: 136,641
Decode time reported by program: 23 ms
```

Result: **PASS**

### 2026-07-28 — Byte-level and property-level round-trip verification

Commands:

```bash
cd $REPO

cmp -s \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply
echo $?

python3 experiment_results/exp3b_zero_attributes/verify_exp3b.py \
  --source testdata/3DGS/3dgs.ply \
  --modified experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  --decoded experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply \
  --output experiment_results/exp3b_zero_attributes/roundtrip_verification.json

stat -c '%n %s bytes' \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply

sha256sum \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  experiment_results/exp3b_zero_attributes/decoded_zeroed_attributes.ply
```

Why:

Use the strongest simple check (`cmp`) and a semantic PLY check. The semantic
check explains count, property order, row order, and float32 value equality
rather than relying only on equal file hashes.

Observed:

```text
cmp exit status: 0
Modified PLY SHA-256:
  8186f8afa6eac3a85a2b1fba29d7bca595d777b2c28b0ae96564ece35f114bc5
Decoded PLY SHA-256:
  8186f8afa6eac3a85a2b1fba29d7bca595d777b2c28b0ae96564ece35f114bc5
Headers identical: yes
Gaussian count preserved: yes
Property order preserved: yes
Changed rows: 0
Changed float32 values: 0
All 8,471,742 float32 values bit-exact: yes
```

Sizes:

```text
Original source PLY: 33,888,499 bytes
Modified PLY:        33,888,499 bytes
Lossless DRC:        33,887,039 bytes
Decoded PLY:         33,888,499 bytes
```

Result: **PASS — byte-for-byte lossless round trip**

### 2026-07-28 — Control comparison with unmodified lossless DRC

Commands:

```bash
cd $REPO

stat -c '%n %s bytes' \
  experiment_results/exp1b_binary_input/binary_input_q0.drc \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc

sha256sum \
  experiment_results/exp1b_binary_input/binary_input_q0.drc \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc

cmp -s \
  experiment_results/exp1b_binary_input/binary_input_q0.drc \
  experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc
echo $?
```

Why:

Determine whether changing ten previously nonzero property groups to repeated
zeros reduced the size relative to the earlier all-lossless encoding of the
unmodified source.

Observed:

```text
Unmodified lossless DRC: 33,887,039 bytes
Modified lossless DRC:   33,887,039 bytes
DRC files byte-identical: no
```

The contents differ, as confirmed by different hashes, but their sizes are
exactly equal. Compared with the binary PLY, the DRC is only 1,460 bytes
smaller (0.004308% reduction; 99.995692% of the PLY size).

Interpretation:

For this build's no-quantization path, replacing the selected values with
zeros did not improve DRC size. This indicates that the lossless attribute
payload format has effectively fixed size for this schema/count, or otherwise
does not exploit these repeated zeros. We report the observed behavior without
generalizing it to other Draco versions or coding paths.

Result: **CONTROL COMPLETE**

## 8. Result summary

Experiment 3B: **PASS**

- GS-Interface changed only the requested stored properties.
- Normals were already zero; ten other targeted properties changed.
- Color coefficients and opacity remained bit-exact.
- Draco used no quantization for any attribute group.
- The decoder preserved the complete modified PLY byte-for-byte.
- Gaussian count, schema, row order, and all float32 bits were preserved.
- Zeroing the selected values did not reduce the lossless DRC size relative
  to the unmodified lossless control.

### 2026-07-28 — GS-Interface dependency check

Commands:

```bash
cd $GS_INTERFACE
python3 --version
python3 -c "import numpy; import plyfile; print('GS-Interface dependencies available')"
sed -n '1,180p' io_3dgs.py
```

Why:

Confirm the Python version and required libraries, then inspect how
GS-Interface loads and exports property arrays.

Observed:

```text
Python 3.14.4
ModuleNotFoundError: No module named 'numpy'
```

Inspection confirmed that `io_3dgs.py` requires both NumPy and `plyfile`,
stores each property under `data[property_name]["data"]`, and exports
properties by dictionary insertion order.

Result: **DEPENDENCIES MISSING — create an experiment-specific virtual
environment and install NumPy plus plyfile before continuing.**

### 2026-07-28 — Create the isolated Python environment

Commands:

```bash
cd $GS_INTERFACE
python3 -m venv .venv-exp3b
.venv-exp3b/bin/python -m pip install numpy plyfile
```

Why:

Keep Experiment 3B dependencies separate from the system Python and other
projects. The first installation attempt was made in the restricted
environment and failed because DNS/network access was unavailable. The same
specific installation command was then approved for network access and
repeated.

Observed:

```text
Successfully installed numpy-2.5.1 plyfile-1.1.4
```

Result: **PASS**

## 9. Chronological index

The actual execution order was:

1. Verify repository, tracked input, header, checksum, and Draco binaries.
2. Check GS-Interface dependencies; discover that NumPy was missing.
3. Create `.venv-exp3b`.
4. Attempt dependency installation in the restricted environment; network
   access failed.
5. Repeat the same scoped installation with approved network access;
   NumPy 2.5.1 and plyfile 1.1.4 installed successfully.
6. Create `zero_attributes.py` and `verify_exp3b.py`.
7. Compile-check the scripts.
8. Attempt the GS-Interface transformation; import-path resolution failed
   before an output PLY was written.
9. Correct the script to locate the sibling GS-Interface repository.
10. Rerun the transformation; GS-Interface output and reload checks passed.
11. Independently verify source versus modified PLY; all requested outputs
    were zero and every untargeted value was bit-exact.
12. Losslessly encode the modified PLY with all quantization options at zero.
13. Decode the DRC.
14. Run byte-level, checksum, and property-level round-trip comparisons; all
    passed.
15. Compare the DRC size with the earlier unmodified lossless control.
16. Write `REPORT.md` and validate the Python and JSON artifacts.

### 2026-07-28 — Create auditable modification and verification programs

Files created:

```text
experiment_results/exp3b_zero_attributes/zero_attributes.py
experiment_results/exp3b_zero_attributes/verify_exp3b.py
```

Why:

- `zero_attributes.py` must use `GaussianModelV2` from GS-Interface, explicitly
  name the 13 targets, refuse to overwrite the source, preserve snapshots of
  every untargeted property, export, reload, and verify.
- `verify_exp3b.py` independently parses binary little-endian float32 PLY files
  using only the Python standard library. It checks that targets became zero,
  untargeted values stayed bit-exact, and the eventual Draco round trip stayed
  bit-exact.

No broad wildcard is used to choose attributes. This prevents accidental
changes to `f_dc`, `f_rest`, or `opacity`.

Result: **FILES CREATED; execution pending**

### 2026-07-28 — First modification attempt stopped on import

Command:

```bash
cd $GS_INTERFACE
.venv-exp3b/bin/python -m py_compile \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zero_attributes.py \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/verify_exp3b.py

.venv-exp3b/bin/python \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zero_attributes.py \
  --input ../Draco-for-3DGS/testdata/3DGS/3dgs.ply \
  --output ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zeroed_attributes.ply
```

Observed:

```text
ModuleNotFoundError: No module named 'io_3dgs'
```

Why it happened:

When Python executes a script by path, it places the script directory—not
necessarily the shell working directory—first on the module search path.
`zero_attributes.py` is in Draco-for-3DGS while `io_3dgs.py` is in the sibling
GS-Interface repository.

Correction:

The script now derives the shared workspace directory from its own absolute
path, verifies that `GS-Interface/io_3dgs.py` exists, and explicitly adds that
directory to the Python module search path before importing
`GaussianModelV2`.

Safety result: **NO OUTPUT PLY WAS WRITTEN; rerun pending**

### 2026-07-28 — GS-Interface modification succeeded

Command:

```bash
cd $GS_INTERFACE
.venv-exp3b/bin/python -m py_compile \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zero_attributes.py \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/verify_exp3b.py

.venv-exp3b/bin/python \
  ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zero_attributes.py \
  --input ../Draco-for-3DGS/testdata/3DGS/3dgs.ply \
  --output ../Draco-for-3DGS/experiment_results/exp3b_zero_attributes/zeroed_attributes.ply
```

Why:

Compile-check both programs, then use GS-Interface to set exactly the 13
named property arrays to float32 zero. The program also reloads its output and
checks targeted, untargeted, schema, count, and order invariants.

Observed:

```text
Gaussian count: 136,641
Property count: 62
All 13 requested properties zero after reload: yes
Untargeted properties preserved: yes
Property order preserved: yes
```

Result: **PASS**

### 2026-07-28 — Independent source-to-modified verification

Commands:

```bash
cd $REPO

python3 experiment_results/exp3b_zero_attributes/verify_exp3b.py \
  --source testdata/3DGS/3dgs.ply \
  --modified experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  --output experiment_results/exp3b_zero_attributes/modification_verification.json

stat -c '%n %s bytes' \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply

sha256sum \
  testdata/3DGS/3dgs.ply \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply

sed -n '1,/end_header/p' \
  experiment_results/exp3b_zero_attributes/zeroed_attributes.ply
```

Why:

Verify the transformation with a separate implementation that does not depend
on GS-Interface, NumPy, or `plyfile`.

Observed:

```text
Original size: 33,888,499 bytes
Modified size: 33,888,499 bytes
Modified SHA-256: 8186f8afa6eac3a85a2b1fba29d7bca595d777b2c28b0ae96564ece35f114bc5
Gaussian count: 136,641
Property count/order preserved: yes
All targeted output values zero: yes
Untargeted changed values: 0
Untargeted properties bit-exact: yes
```

Per-target finding:

- `x`, `y`, `z`, all three scale properties, and all four rotation properties
  each changed in all 136,641 rows.
- `nx`, `ny`, and `nz` were already numeric zero in all source rows, so
  assigning zero did not change their float32 bits.

Result: **PASS — safe to begin lossless Draco encoding**

### 2026-07-28 — Lossless Draco encode

Command:

```bash
cd $REPO

./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i experiment_results/exp3b_zero_attributes/zeroed_attributes.ply \
  -o experiment_results/exp3b_zero_attributes/zeroed_attributes_lossless.drc \
  -qp 0 \
  -qn 0 \
  -qfd 0 \
  -qfr1 0 \
  -qfr2 0 \
  -qfr3 0 \
  -qo 0 \
  -qs 0 \
  -qr 0 \
  -cl 7
```

Why:

Encode the deliberately modified model without applying quantization to any
attribute group.

Observed encoder configuration:

```text
Compression level = 7
Positions: No quantization
Normals: No quantization
f_dc: No quantization
f_rest_1: No quantization
f_rest_2: No quantization
f_rest_3: No quantization
Opacity: No quantization
Scale: No quantization
Rotation: No quantization
```

Observed result:

```text
Encode time reported by program: 60 ms
Encoded size: 33,887,039 bytes
```

Interpretation:

The encoded size is almost the same as the fixed-width binary PLY size. The
earlier hypothesis that repeated zeros might substantially reduce this
lossless DRC is not supported by the encoded size. This fork's no-quantization
path appears to preserve/store the float32 attribute payload with very little
size reduction. Final size comparisons will be recorded after decoding.

Result: **PASS**
