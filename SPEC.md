# Apple `.ir` File Format Specification

The `.ir` file format is a proprietary Apple binary container used for Spatial Audio datasets (HRIR, BRIR, SEIR, Reverb). 

## 1. Top-Level File Structure

The file consists of three contiguous sections:

1. **Header (4 bytes):** 32-bit unsigned integer (Little-Endian) specifying the length of the metadata block.
2. **Metadata Block (`length` bytes):** An Apple Binary Property List (`bplist00`) containing the dataset parameters.
3. **Audio Payload (Remaining bytes):** A flat array of uncompressed binary records containing coordinates, delays, and raw PCM filter coefficients.

---

## 2. Metadata Block (bplist00)

Located at offset `0x04`, the metadata is standard Apple binary plist format. 
The dictionary contains the following critical keys governing the payload structure:

* `TotalNumCoordinates` *(integer)*: The total number of spatial measurement records in the payload.
* `NumChannels` *(integer)*: The number of audio channels per record.
* `FilterLength` *(integer)*: The number of PCM impulse response samples per channel.
* `Dimensions` *(array of dicts)*: Defines the coordinate axes (e.g., Elevation, Azimuth). The count of items here equals `num_dims`.
* `CoefficientFormat` *(string)*: Data type of the raw PCM samples (usually `"int16"` or `"float32"`).
* `DelayFormat` *(string)*: Data type of the channel delays (usually `"float32"`).
* `FilterScaleFactor` *(float)*: A multiplier used to convert integer PCM back to normalized floating-point `[-1.0, 1.0]` values.
* `SampleRate` *(float)*: The sampling rate of the impulses (e.g., `48000.0`).

---

## 3. Audio Payload Layout

Immediately following the bplist is an array of exactly `TotalNumCoordinates` records. There is no padding between records.

Each record maps to a single spatial coordinate and is structured internally as follows:

| Offset (relative) | Field | Count | Type | Size (Bytes) |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | Coordinates | `num_dims` | `float32` | `num_dims * 4` |
| `Coordinates End` | Delays | `NumChannels` | `DelayFormat` (e.g. `float32`) | `NumChannels * 4` |
| `Delays End` | Raw PCM Coefficients | `NumChannels * FilterLength`| `CoefficientFormat` (e.g. `int16`) | `NumChannels * FilterLength * 2` |

### 3.1 Coefficient Planar Layout
The raw PCM samples are stored in **Planar Layout** (non-interleaved). 
This means all `FilterLength` samples for Channel 0 are provided sequentially, followed by all `FilterLength` samples for Channel 1.

```c
// Example structural visualization for a single record in C
struct IRRecord {
    float32_t coordinates[num_dims];
    float32_t delays[NumChannels];
    
    // Planar raw PCM samples:
    // Left[0...FilterLength-1], then Right[0...FilterLength-1]
    int16_t   coefficients[NumChannels][FilterLength]; 
};
```