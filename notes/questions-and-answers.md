# Draco-for-3DGS Questions and Answers

## Which commit introduced each custom 3DGS attribute, and how does it differ from upstream Google Draco?

The custom attributes were introduced in two stages:

- Commit `b96f722` (`finish all`, 2023-11-22) introduced `F_DC`, a combined `F_REST`, `OPACITY`, `SCALE`, and `ROT`.
- Commit `1aa876d` (`able to set different quantizaton bits to each order of SH`, 2024-03-05) replaced the combined `F_REST` with `F_REST_1`, `F_REST_2`, and `F_REST_3`.

Upstream Google Draco defines standard named attributes such as position, normal, color, and texture coordinates, and uses `GENERIC` for application-specific data. This fork adds named 3DGS attribute types, custom PLY parsing and writing, separate command-line quantization controls, and explicit spherical-harmonic band handling.

The custom type numbers and meanings are specific to this fork. An ordinary upstream Draco decoder should not be expected to decode these custom attributes correctly.

## Why are upstream dependency entries still in `.gitmodules` but absent from `git submodule status`?

The GoogleTest, Eigen, TinyGLTF, and filesystem entries were copied into `.gitmodules` in the first repository commit, but there are no matching mode-`160000` gitlink entries in the current Git tree.

A working Git submodule requires both an entry in `.gitmodules` and a gitlink in the repository tree. Only `submodules/3DGS-Interface` has a gitlink, so it is the only entry reported by `git submodule status`. The four upstream dependency entries are stale or incomplete inherited metadata.

## Is a valid small 3DGS input already present under `testdata/3DGS`, and what spherical-harmonic degree does it use?

Yes. `testdata/3DGS/3dgs.ply` is a valid input and successfully completes a native encode/decode round trip.

It contains:

- 136,641 Gaussians
- 3 `f_dc` properties
- 45 `f_rest` properties
- opacity
- 3 scale components
- 4 rotation-quaternion components

There are 48 spherical-harmonic coefficients across the three color channels:

```text
3 * (3 + 1)^2 = 48
```

Therefore, the input uses spherical-harmonic degree 3. The 45 non-DC coefficients are divided into 9, 15, and 21 values for degrees 1, 2, and 3 respectively.

The file is a useful repository sample, although at approximately 33 MB it is not especially small. A smaller fixture should eventually be derived for fast automated tests.

## Can the native encoder and decoder build without initializing any submodule?

Yes, for the core codec. A clean build succeeded with all submodules uninitialized using:

```bash
cmake -S . -B /tmp/draco-3dgs-clean-build \
  -DDRACO_TESTS=OFF \
  -DDRACO_TRANSCODER_SUPPORTED=OFF \
  -DCMAKE_BUILD_TYPE=Release

cmake --build /tmp/draco-3dgs-clean-build \
  --target draco_encoder draco_decoder
```

Both native tools built successfully. The complete 136,641-point sample also encoded and decoded successfully. Tests and optional transcoder/glTF functionality may still require upstream dependencies, but the core 3DGS encoder and decoder do not.

## Which Python and PyTorch versions were used by the original author?

The exact versions are not documented. The repository has no `requirements.txt`, Conda environment, Python lockfile, or recorded `torch.__version__`.

Committed bytecode filenames demonstrate that CPython 3.7 and CPython 3.11 were used at some point. They do not establish which version was the author's primary environment.

The exact PyTorch version cannot be recovered from the repository. The CUDA and Apple MPS code paths provide compatibility clues, but not enough evidence for a precise version. Assigning a specific PyTorch version would therefore be speculation.

## Can PLY-to-ASCII conversion be done entirely with NumPy and `plyfile`, avoiding GPU-backed PyTorch tensors?

Yes. PyTorch is unnecessary for this conversion. The existing converter uses tensors only to store arrays, transpose and flatten feature data, and convert the result back to CPU NumPy arrays.

The equivalent operations can be performed directly with NumPy:

```python
features_dc_out = features_dc.transpose(0, 2, 1).reshape(len(features_dc), -1)
features_rest_out = features_rest.transpose(0, 2, 1).reshape(len(features_rest), -1)

attributes = np.concatenate(
    [
        xyz,
        features_dc_out,
        features_rest_out,
        opacity,
        scales,
        rotations,
    ],
    axis=1,
)
```

`plyfile` can then write the assembled data as an ASCII PLY. This removes CUDA/MPS requirements, autograd parameters, GPU transfers, and unnecessary tensor allocations.

## Does splitting `f_rest` into three attribute bands materially improve compression, or only permit separate quality control?

The split definitely permits separate quality control, but it does not automatically guarantee better compression.

Possible benefits include:

- assigning fewer bits to less visually important higher SH orders
- adapting each quantizer to the numerical range of its band
- dropping higher-order bands independently

Possible costs include:

- additional attribute headers and coding contexts
- independent prediction and entropy coding for each attribute
- losing compression opportunities based on correlations between bands

The demonstrated purpose is independent quantization and deletion of SH orders. Whether the split materially improves compression requires a controlled rate-distortion experiment comparing combined and split encodings at equal rendered quality, rather than merely at equal bit depth.

## Are the custom 3DGS attributes encoded compatibly by both native and WASM builds?

Not by the currently committed artifacts.

A stream produced by the freshly built native encoder was tested with the committed Node/WASM decoder. The WASM decoder read the standard position and normal attributes, then failed at the custom attributes with:

```text
Failed to decode point attributes.
```

The generated JavaScript bindings also expose only the upstream attribute enum names and do not expose `F_DC`, `F_REST_1`, `F_REST_2`, `F_REST_3`, `OPACITY`, `SCALE`, or `ROT`.

A new WASM build from the modified C++ source may be made compatible, but it needs updated WebIDL/bindings, regenerated encoder and decoder artifacts, and native-to-WASM plus WASM-to-native cross-tests. The bundled WASM files should not currently be treated as compatible with the custom native bitstream.

## What validation metric should be used first: attribute error, rendered PSNR, SSIM, LPIPS, or a combination?

Validation should be performed in layers.

First, validate structure and attributes:

- equal Gaussian count
- equal property layout
- no NaN or infinite values
- valid or renormalized quaternions
- per-attribute MAE, RMSE, and maximum error

This stage catches codec, schema, ordering, and serialization bugs. Attribute error alone is not sufficient for final quality evaluation because equal coefficient errors can have very different effects on a rendered image.

Next, validate rendered images using a combination:

- PSNR as the primary conventional pixel-distortion metric
- SSIM as a structural-similarity companion
- LPIPS as a perceptual-similarity companion

Finally, report rate-distortion results by plotting compressed size or bits per Gaussian against PSNR, SSIM, and LPIPS.

## Why may position, spherical-harmonic coefficients, opacity, scale, and rotation need different quantization precision instead of one shared bit depth?

These attributes have different numerical ranges, representations, activation functions, and effects on the rendered image. Giving every attribute the same bit depth therefore does not give every attribute the same numerical or visual accuracy.

### Position

Position determines where a Gaussian appears. Small errors can move silhouettes and edges, disturb geometry, or create ghosting. Its effective precision also depends on scene extent: a fixed-bit quantization grid produces larger spatial steps in a large scene than in a small scene.

### Spherical-harmonic coefficients

Spherical-harmonic coefficients control view-dependent color. The DC coefficients determine base color and are normally more important than higher-order coefficients. Higher orders add directional detail and may tolerate larger errors. Different SH bands can also have substantially different value distributions and ranges.

### Opacity

Opacity controls how strongly a Gaussian contributes during compositing. Errors can accumulate through many overlapping Gaussians along a ray. An opacity change can make surfaces appear too transparent, too dense, or change which deeper Gaussians remain visible.

### Scale

Scale controls the ellipsoid's size and screen-space footprint. Errors can blur details, create gaps, or introduce excessive overlap. Scale may be stored in a transformed domain, so a small error in the stored value can become a multiplicative error after its activation function is applied.

### Rotation

Rotation is represented by four quaternion components that jointly describe an orientation. Quantization can disturb the quaternion's unit length, so it may need renormalization. Rotation error is particularly visible for strongly anisotropic Gaussians, while it has little effect on nearly spherical ones.

### Conclusion

Quantization precision should account for both:

- numerical behavior: range, distribution, representation, and activation function
- rendered sensitivity: how an error changes the final image

That is why this fork provides separate quantization controls for position, DC color, individual SH bands, opacity, scale, and rotation rather than one global shared bit depth.
