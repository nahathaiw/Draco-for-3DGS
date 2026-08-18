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
**[!] You should change the 3DGS data to ASCII format before you encode.**

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
