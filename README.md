# Draco for 3D Gaussian Splatting

This is a variant of [Google Draco Compression](https://google.github.io/draco/) to support [original 3D Gaussian splatting (3DGS)](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) content.

Draco is an open-source library for compressing and decompressing 3D geometric meshes and point clouds. It is intended to improve the storage and transmission of 3D graphics.

However, this project is only focused on encode and decode 3DGS, so compressing 3D meshes or 3D point cloud is not supported.

## Build (C++ execution)

### Build (Ubuntu and MACOS)
```bash
mkdir build_dir && cd build_dir
cmake ../
make
```

## Build (Javascript WebAssembly) (Test in MACOS)
```bash
mkdir build_dir && cd build_dir
export EMSCRIPTEN=/path_to_emsdk/upstream/emscripten
# for example: export EMSCRIPTEN=/Users/syjintw/Desktop/MMSys25_RU/emsdk/upstream/emscripten
cmake ../ -DCMAKE_TOOLCHAIN_FILE=/path_to_emsdk/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake -DDRACO_WASM=ON
# for example: cmake ../ -DCMAKE_TOOLCHAIN_FILE=/Users/syjintw/Desktop/MMSys25_RU/emsdk/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake -DDRACO_WASM=ON
make
java -jar ../additional/closure-compiler-v20210302.jar --compilation_level SIMPLE --js draco_decoder.js --js_output_file draco_wasm_wrapper.js
```

## Usage

Converting 3DGS data to ASCII is the compatibility-safe input workflow. The
standard binary little-endian, 62-float 3DGS schema used in these experiments
also works directly and produces the same lossless bitstream, but other binary
PLY schemas are not guaranteed to work. See
[Experiment 1B](experiment_results/7-28-26exp/exp1b_binary_input/REPORT.md).

## Change binary format to ASCII format
```bash
python ./mytool/3DGS_pcd_to_draco_pcd.py -i ./myData/ficus.ply -o ./myData/ficus_3dgs.ply
```

## Encode (C++ execution)
### Simple
```bash
./build_dir/draco_encoder -point_cloud \
-i ./myData/ficus_3dgs.ply \
-o ./myData/ficus_3dgs_compressed.drc
```

### More complex setup
```bash
./build_dir/draco_encoder -point_cloud \
-i ./myData/ficus_3dgs.ply \
-o ./myData/ficus_3dgs_compressed.drc \
-qp 16 \
-qfd 16 -qfr1 16 -qfr2 16 -qfr3 16 \
-qo 16 \
-qs 16 -qr 16 \
-cl 10
```

### Lossless attributes and skipping 3DGS attributes

Set an attribute's quantization value to `0` to disable quantization and retain
its original values. This keeps the attribute in the encoded point cloud; it is
not the same as skipping the attribute.

The encoder can omit normals, scales, or rotations with `--skip`:

```bash
# Omit rotations from the encoded file.
./build_dir/draco_encoder -point_cloud \
-i ./myData/ficus_3dgs.ply \
-o ./myData/ficus_3dgs_without_rotation.drc \
--skip ROT

# Omit normals and scales from the encoded file.
./build_dir/draco_encoder -point_cloud \
-i ./myData/ficus_3dgs.ply \
-o ./myData/ficus_3dgs_without_normal_and_scale.drc \
--skip NORMAL --skip SCALE
```

Supported `--skip` values are `NORMAL`, `TEX_COORD`, `GENERIC`, `SCALE`, and
`ROT`. A skipped attribute is deleted before encoding and will therefore not be
present after decoding. The encoder prints `Normal: Skipped`, `Scale: Skipped`,
or `Rotation: Skipped` when the corresponding 3DGS attribute was found and
removed.

To encode the 3DGS attributes without quantization, use zero for their
quantization options:

```bash
./build_dir/draco_encoder -point_cloud \
-i ./myData/ficus_3dgs.ply \
-o ./myData/ficus_3dgs_lossless_attributes.drc \
-qp 0 -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
-qo 0 -qs 0 -qr 0 \
-cl 10
```

After decoding, compare the source and decoded PLY data with a PLY-aware tool
instead of relying only on a byte-for-byte `diff`: serialization details such as
headers or numeric formatting may differ even when attribute values match.

## Experiment results and artifacts

The repository records experiment methods, terminal commands, verification
scripts, and machine-readable results under `experiment_results/`. Large PLY
files, Draco bitstreams, build trees, and raw command logs are kept locally and
ignored by Git; the smaller reproducibility artifacts are version-controlled.

| Date | Experiment | Main result | Documentation and evidence |
|---|---|---|---|
| 2026-07-28 | Full lossless 3DGS round trip | All 62 properties and 136,641 Gaussian rows were byte-identical after zero-quantization encode/decode. | [Report](experiment_results/7-28-26exp/exp1_lossless/REPORT.md), [checksums](experiment_results/7-28-26exp/exp1_lossless/SHA256SUMS.txt) |
| 2026-07-28 | Direct binary PLY input | The tested binary PLY encoded directly and produced the same `.drc` as verified ASCII input. | [Report](experiment_results/7-28-26exp/exp1b_binary_input/REPORT.md), [comparison](experiment_results/7-28-26exp/exp1b_binary_input/comparison.txt) |
| 2026-07-28 | Selective 16-bit SH/color quantization | Geometry, opacity, scale, and rotation stayed exact; SH/color became lossy. The `.drc` was 42.39% smaller than the source PLY. | [Report](experiment_results/7-28-26exp/exp3_selective_sh16/REPORT.md), [comparison script](experiment_results/7-28-26exp/exp3_selective_sh16/compare_ply.py), [results](experiment_results/7-28-26exp/exp3_selective_sh16/comparison.json) |
| 2026-07-28 | Zero selected non-color attributes | The artificially zeroed model survived a fully lossless round trip, but zeroing did not reduce the lossless `.drc` size. | [Report](experiment_results/7-28-26exp/exp3b_zero_attributes/REPORT.md), [log](experiment_results/7-28-26exp/exp3b_zero_attributes/log.md), [round-trip results](experiment_results/7-28-26exp/exp3b_zero_attributes/roundtrip_verification.json) |
| 2026-07-28 | Replace rotation with identity quaternions | Every rotation became `(1,0,0,0)` while untargeted values remained exact; the modified model then round-tripped byte-for-byte. | [Report](experiment_results/7-28-26exp/exp3c_identity_rotation/REPORT.md), [log](experiment_results/7-28-26exp/exp3c_identity_rotation/log.md), [round-trip results](experiment_results/7-28-26exp/exp3c_identity_rotation/roundtrip_verification.json) |
| 2026-07-28 | Skip rotation | `rot_0..3` were removed, all retained values and row order stayed exact, and the `.drc` became 6.451617% smaller than the lossless baseline. | [Report](experiment_results/7-28-26exp/exp4_skip_rotation/REPORT.md), [log](experiment_results/7-28-26exp/exp4_skip_rotation/log.md), [verification](experiment_results/7-28-26exp/exp4_skip_rotation/skip_rotation_verification.json) |
| 2026-07-29 | Skip normal and scale | Six properties were removed, every retained value stayed exact, and the `.drc` became 9.677434% smaller than the lossless baseline. | [Report](experiment_results/7-29-26exp/exp1_skip_normal_scale/REPORT.md), [implementation guide](experiment_results/7-29-26exp/exp1_skip_normal_scale/HOW_SKIP_HANDLING_WORKS.md), [log](experiment_results/7-29-26exp/exp1_skip_normal_scale/log.md), [verification](experiment_results/7-29-26exp/exp1_skip_normal_scale/skip_verification.json) |
| 2026-08-13 | Hotdog full lossless round trip | All 9,224,546 values across 148,783 Gaussians were exact, but the `.drc` was only 0.003957% smaller than the source PLY. | [Report](experiment_results/8-13-26exp/hotdog_lossless/REPORT.md) |
| 2026-08-18 | Hotdog: keep only position, color, and opacity | Normal, scale, and rotation were removed. All 7,736,716 retained values and row order stayed exact; the `.drc` became 16.129050% smaller than the full lossless baseline. | [Reproduction guide](experiment_results/8-18-26/hotdog_position_color_opacity/README.md), [report](experiment_results/8-18-26/hotdog_position_color_opacity/REPORT.md), [complete command log](experiment_results/8-18-26/hotdog_position_color_opacity/log.md), [verification](experiment_results/8-18-26/hotdog_position_color_opacity/selective_verification.json) |

### Experiment directory map

```text
experiment_results/
├── 7-28-26exp/
│   ├── exp1_lossless/             # Full zero-quantization round trip
│   ├── exp1b_binary_input/        # Binary input versus ASCII input
│   ├── exp3_selective_sh16/       # Lossy SH/color, lossless other attributes
│   ├── exp3b_zero_attributes/     # Zero selected values before lossless coding
│   ├── exp3c_identity_rotation/   # Replace rotation with identity quaternion
│   └── exp4_skip_rotation/        # Remove rotation from the bitstream
├── 7-29-26exp/
│   └── exp1_skip_normal_scale/    # Remove normal and scale
├── 8-13-26exp/
│   └── hotdog_lossless/           # Full Hotdog lossless timing test
└── 8-18-26/
    └── hotdog_position_color_opacity/  # Reproducible selective Hotdog test
```

For a new experiment, follow the 2026-08-18 layout: include a reproduction
`README.md`, a result-focused `REPORT.md`, a chronological `log.md`, scripts,
timings, sizes, checksums, and JSON verification evidence. Do not commit the
generated model files.

### Reproduce the Hotdog position/color/opacity experiment

The Hotdog selective-lossless experiment keeps position, all spherical-harmonic
color coefficients, and opacity while omitting normal, scale, and rotation.

Place the dataset at:

```text
testdata/3DGS/hotdog/checkpoint/point_cloud/iteration_30000/point_cloud.ply
```

Then run the complete build, encode, decode, timing, and verification workflow
from the repository root:

```bash
bash experiment_results/8-18-26/hotdog_position_color_opacity/run_experiment.sh
```

The retained attributes use zero quantization and are verified bit-for-bit. On
the recorded Hotdog run, all 7,736,716 retained float32 values were exact and
the selective bitstream was 16.129050% smaller than the all-attribute lossless
baseline.

See the experiment's
[`README.md`](experiment_results/8-18-26/hotdog_position_color_opacity/README.md)
for prerequisites and reproduction instructions, and
[`REPORT.md`](experiment_results/8-18-26/hotdog_position_color_opacity/REPORT.md)
for the complete results and limitations.

## Development notes (2025-07-23)

1.
No need to think about the compression ratio.

### Draco-for-3DGS
Check changing 16 bits to 0 bits. Zero bits means lossless. If it is set to 0,
no information should be lost and the order should be kept. Use `diff` first; if
the files differ, use [GS-Interface](https://github.com/SYJINTW/GS-Interface).

### Draco original
2. check if we compress the mesh . Try to compress the colored mesh (yuan chun will give color mesh later)
- make sure that we use lossless way to (check in the original readme) and make sure that the order will not change
- way to check diff (cmd to see if the two data are differnet) maybe write a reader to checkk if tthe informatin are the same
- (the reader trimesh (python library) to check if the information of the mesh are the same like vertex face triancgle color if they are the same)


### Draco-for-3DGS
3. change all the information except the sh (color) change it all to 0 but keep the color and compress using the lossless way
then i compress it with the lossless way and check if the two data ( check the file size )
TO CHANGE THE 3DGS INFORMAION WE CAN USE https://github.com/SYJINTW/GS-Interface.git

4. Check the draco 3dgs code
- small experiment try to not compress rotation ex delete the rotation part(like dont need to read the rotation)

feed the original 3dgs --> compress it --> then decode it --> after we unpacked we wont have the rotation


## Decode (C++ execution)
```bash
./build_dir/draco_decoder \
-i ./myData/ficus_3dgs_compress.drc \
-o ./myData/ficus_3dgs_distorted.ply
```

## Decode (Javascript)

Check the html file (`/draco_adjusted/javascript/time_draco_decode.html`)
There are some important path need to change, and you can search them using `//! [YC]` as the searching keyword. Good Luck!!

Open the web server using the following command in the root folder
```
python -m http.server
```


# For Experiment
## Encode (Using my_encode.py and json file)
```bash
python my_encoder.py -jp ../myJson/template_sh0.json
```

## Decode (Using my_decode.py and json file)
```bash
python my_decoder.py -jp ../myJson/template.json
```

## Configuration json file
Based on the template json file at `myJson/template.json`


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

<!-- ## License

[MIT](https://choosealicense.com/licenses/mit/) -->
