# Apple `.ir` File Format Specification

The `.ir` file format is Apple's binary container for Spatial Audio impulse-response datasets (HRIR, BRIR, SEIR, Reverb), implemented in `libAudioDSPCore` (within `AudioDSPCore`).

---

## 1. Top-Level File Structure

An `.ir` file consists of three contiguous sections:

1. **Header (4 bytes):** 32-bit unsigned integer (Little-Endian) specifying the byte length of the binary metadata block.
2. **Metadata Block (`length` bytes):** Apple Binary Property List (`bplist00`, `CFPropertyList` binary format 1.0) containing dataset metadata and schema definitions.
3. **Audio Payload (Remaining bytes):** A contiguous array of exactly `TotalNumCoordinates` spatial records containing coordinate positions, PCM filter coefficients, and channel delays.

```
+---------------------------+-----------------------------------+------------------------------------------+
| Header: uint32_le (4 B)   | Metadata Block: bplist00 (length) | Audio Payload (TotalNumCoordinates recs) |
+---------------------------+-----------------------------------+------------------------------------------+
```

---

## 2. Metadata Block (`bplist00`)

Located immediately at byte offset `0x04`, the metadata dictionary defines all parameters governing the audio payload:

### Critical Structural Keys
* `TotalNumCoordinates` *(integer)*: Total count of spatial coordinate measurement records in the payload.
* `NumChannels` *(integer)*: Number of audio channels per record (e.g. `2` for binaural).
* `FilterLength` *(integer)*: Number of PCM impulse response samples per channel.
* `CoefficientFormat` *(string)*: Data type of raw PCM coefficients: `"int16"` (2 bytes, Little-Endian signed short) or `"float32"` (4 bytes, Little-Endian IEEE 754 float).
* `DelayFormat` *(string)*: Data type of channel delay values, typically `"float32"` (4 bytes, Little-Endian float).
* `SampleRate` *(float)*: Sampling rate of the impulses in Hz (e.g., `48000.0`).
* `FilterScaleFactor` *(float)*: Multiplier used to scale integer PCM values back to normalized floating-point `[-1.0, 1.0]`. Defaults to `1.0`.
* `Dimensions` *(array of dicts)*: Defines each spatial axis. The length of this array equals `num_dims`.

### Recognized Coordinate Names in `Dimensions`
Apple's coordinate parser (`IR::IRCoordinates::getParameterString`) recognizes up to 9 dimension axes:
* `"Azimuth"` (0)
* `"Elevation"` (1)
* `"Distance"` (2)
* `"ChannelAzimuth"` (3)
* `"ChannelElevation"` (4)
* `"DeviceOrientation"` (5)
* `"Generic"` (6)
* `"InputChannel"` (7)
* `"Size"` (8)

Each dictionary in `Dimensions` contains:
* `Name` *(string)*: One of the supported coordinate axis names.
* `DefaultValue` *(float)*: Default coordinate value.
* `Periodicity` *(float)*: Wrap-around period in degrees (e.g., `360.0` for cyclical azimuth), or `0.0`.
* `Interpolation` *(integer)*: Spatial interpolation mode (`0` = Nearest, `1` = Linear, `2` = Spherical/VBAP).

### Optional Metadata Keys
* `AudioChannelLayoutTag` *(integer)*: CoreAudio `AudioChannelLayoutTag` for speaker positioning or Ambisonics/HOA ordering.
* `Description` *(string)*: Human-readable dataset description.
* `UserData` *(dict)*: Resampling and filter options (`ResamplerType`, `quality`, `rmLatencySamples`, `rmPostRingSamples`, `DelayBakedInCoeffs`).
* `TriangulationData` *(dict)*: Vector-Base Amplitude Panning (VBAP) triangulation mesh data (`NumTriangulations`, `TriVertices`, `TriAssignment`, `TriBinLengths`, `TriBinSerial`).
* `ImpulseResponses` *(array of dicts)*: Used in consolidated multi-IR container files, where each item specifies an IR `Type` and `DataLengthBytes`.

---

## 3. Audio Payload Layout

Immediately following the `bplist` at byte offset `4 + length` is a contiguous sequence of `TotalNumCoordinates` records without padding.

### 3.1 Record Internal Structure

Each spatial record contains the coordinates followed by **per-channel blocks**. In Apple's implementation, **each channel's coefficients are immediately followed by that channel's delay value**:

| Relative Offset | Field | Count | Type | Size (Bytes) |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | Coordinates | `num_dims` | `float32` | `num_dims * 4` |
| `Coordinates End` | Channel 0 Coefficients | `FilterLength` | `CoefficientFormat` (`int16`/`float32`) | `FilterLength * sizeof(coeff)` |
| `Ch 0 Coeffs End` | Channel 0 Delay | `1` | `DelayFormat` (`float32`) | `4` |
| `Ch 0 Delay End` | Channel 1 Coefficients | `FilterLength` | `CoefficientFormat` (`int16`/`float32`) | `FilterLength * sizeof(coeff)` |
| `Ch 1 Coeffs End` | Channel 1 Delay | `1` | `DelayFormat` (`float32`) | `4` |
| `...` | `...` | `...` | `...` | `...` |
| `Ch N-1 End` | Channel N-1 Delay | `1` | `DelayFormat` (`float32`) | `4` |

### 3.2 Total Record Size

$$\text{Bytes Per Record} = (\text{num\_dims} \times 4) + \text{NumChannels} \times \Big(\text{FilterLength} \times \text{sizeof(CoefficientFormat)} + \text{sizeof(DelayFormat)}\Big)$$

For a standard 2-channel `int16` impulse response with 1 coordinate dimension (Azimuth) and `FilterLength = 768`:
* Coordinate: $1 \times 4 = 4\text{ bytes}$
* Channel 0: $(768 \times 2) + 4 = 1540\text{ bytes}$
* Channel 1: $(768 \times 2) + 4 = 1540\text{ bytes}$
* Total per record: $4 + 1540 + 1540 = 3084\text{ bytes}$

### 3.3 Structural Representation (C/C++)

```c
// Layout of a single channel's block within a record
struct IRChannelData {
    int16_t   coefficients[FilterLength]; // or float32_t when CoefficientFormat == "float32"
    float32_t delay;                      // Single channel delay (DelayFormat)
};

// Layout of a single spatial record
struct IRRecord {
    float32_t     coordinates[num_dims];
    IRChannelData channels[NumChannels];
};
```
