# Hotdog Lossless Round-Trip Report

## Goal

Measure each stage of a lossless Draco-for-3DGS round trip on the Hotdog scene
and verify that the decoded Gaussian data is identical to the input.

## Input

The test used the Gaussian point cloud at:

```text
testdata/3DGS/hotdog/checkpoint/point_cloud/iteration_30000/point_cloud.ply
```

The local Hotdog dataset is excluded from Git because it contains a large model
checkpoint, rendered images, TensorBoard data, and generated geometry. The input
PLY had these properties:

- Binary little-endian PLY
- 148,783 Gaussians
- 62 float32 properties per Gaussian
- 36,899,715 bytes
- SHA-256: `6627c742839390c92d2e272295e3dbaa2b55b278c7b797f9451c3333a3f65fcd`

## Lossless configuration

Every attribute quantizer was disabled by setting its bit count to `0`:

```bash
./build-local/draco_encoder-1.5.6 \
  -point_cloud \
  -i /tmp/hotdog_ascii.ply \
  -o /tmp/hotdog_q0.drc \
  -qp 0 -qn 0 \
  -qfd 0 -qfr1 0 -qfr2 0 -qfr3 0 \
  -qo 0 -qs 0 -qr 0 \
  -cl 7
```

The encoder reported `No quantization` for positions, normals, base color, all
three higher-order spherical-harmonic groups, opacity, scale, and rotation.

## Timings

GNU `time` measured each command separately on 2026-08-13:

| Stage | Wall time | User time | System time | Peak RSS |
|---|---:|---:|---:|---:|
| Binary PLY to ASCII preparation | 3.72 s | 3.62 s | 0.09 s | 10,484 KiB |
| Lossless encoding | 0.91 s | 0.69 s | 0.21 s | 253,212 KiB |
| Decoding | 0.15 s | 0.03 s | 0.10 s | 125,456 KiB |
| Whole-file `cmp` | 0.02 s | 0.00 s | 0.01 s | 1,820 KiB |
| Attribute-aware verification | 5.07 s | 5.05 s | 0.01 s | 16,120 KiB |

Preparation, encoding, and decoding took 4.78 seconds in total. Draco's
internal timers reported 55 ms for compression and 27 ms for decompression;
the end-to-end measurements also include file parsing and writing.

## Sizes

| File | Size |
|---|---:|
| Original binary PLY | 36,899,715 bytes |
| Temporary ASCII PLY | 180,928,370 bytes |
| Lossless Draco bitstream | 36,898,255 bytes |
| Decoded binary PLY | 36,899,715 bytes |

The Draco bitstream saved 1,460 bytes, a reduction of approximately 0.003957%.
Disabling all quantization therefore preserved the data exactly but produced
essentially no size reduction for this scene.

## Verification

The source and decoded PLY files had the same SHA-256 digest. A parsed,
attribute-aware comparison also confirmed:

- Gaussian counts were both 148,783.
- All 62 properties had the same names and order.
- All 9,224,546 float32 values were bit-identical.
- No position row changed, so Gaussian ordering was preserved.
- Position, normal, `f_dc`, every `f_rest` group, opacity, scale, and rotation
  were exact.
- The PLY headers were identical.

## Conclusion

The Hotdog scene completes a fully lossless Draco-for-3DGS round trip when all
quantization options are set to zero. The tradeoff is that this mode offers
negligible compression for this dataset.
