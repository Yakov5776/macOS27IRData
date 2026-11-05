# Apple IR container

## Container and records

At offset 0 is a **little-endian uint32** metadata byte length L, followed by L bytes of binary property list beginning `bplist00`. The ordinary single-dataset payload begins at `4 + L`.

For D dimensions, C channels, N filter taps, coefficient width W, and optional delay width T:

```text
record = float32_le coordinates[D]
         repeat C times:
             coefficients[N]  # int16_le or float32_le
             delay            # float32_le when DelayFormat is present
record_bytes = 4*D + C*(N*W + T)
file_bytes = 4 + L + TotalNumCoordinates*record_bytes
```

There is no padding in any supplied file. Coordinates follow `Dimensions` order, not a fixed azimuth/elevation order. HRIR stores **Elevation, Azimuth**; SEIR stores **Elevation, Azimuth, InputChannel**. Coefficients are planar within each record, and each channel's delay immediately follows its taps. Delay values are samples at SampleRate, not seconds. All eleven supplied files use int16 coefficients, float32 delays, and 48 kHz. Float32 coefficients and absent delay blocks are supported by the research parser but are not represented by an original sample here.

The shared reader rejects bad lengths, trailing/truncated data, unsupported encodings and nonfinite record values instead of silently treating unknown formats as float or missing records as zeros.

## Metadata

| Key | Meaning and scope |
| --- | --- |
| TotalNumCoordinates | Number of records; not necessarily unique directions (SEIR has another axis) |
| NumChannels | Filters per record; two for HRIR/BRIR/Reverb, one for SEIR |
| FilterLength | Taps per channel |
| SampleRate | Coefficient and delay sample rate |
| CoefficientFormat | `int16` or `float32` in the inspected reader |
| DelayFormat | `float32` in supplied files; absence means no serialized delay field |
| FilterScaleFactor | Multiplier on decoded values, including floating-point coefficients; not a guarantee of [-1,1] bounds |
| Dimensions | Name, DefaultValue, Periodicity, Interpolation for each serialized coordinate |
| UserData | Processing metadata described below |
| ExtendedMetadata | HRIR sphericalGridWeights and sphericalGridOrder; retain verbatim |
| AudioChannelLayoutTag | Optional CoreAudio layout; not supplied ear positions |
| Type / DataLengthBytes | Also used by consolidated containers; ordinary samples have Type=0/DataLengthBytes=0 where present |

Native `IRCoordinates::getParameterString` recognizes Azimuth, Elevation, Distance, ChannelAzimuth, ChannelElevation, DeviceOrientation, Generic, InputChannel, and Size. Recognition of a coordinate name does not prove every consumer implements it. Supplied room assets use 0, HRIR angular axes use 1 **and triangulation**, and SEIR uses 1 for angles and 0 for InputChannel. Spherical interpolation is also a separate IRDataAttributes setting.

## Scaling and timing

Three useful representations must stay distinct:

1. Raw stored values.
2. Stored-amplitude coefficients: `raw * FilterScaleFactor`.
3. Recovered loader coefficients: `raw * FilterScaleFactor / DiffuseFieldPowerRMS`, when that field exists and its absolute value exceeds `2^-23`; otherwise use the scale alone.

Both HRIRs specify RMS 1.412538. Do not peak-normalize or clip these filters.

`DelayBakedInCoeffs` means delay is already in the coefficients; it does **not** mean a serialized delay block is absent. General HRIR has ModelingDelay=48 and baked delay; Movie HRIR has separate fractional delays and no ModelingDelay key. General has 128 taps, Movie 64. The stored delay values remain available even when an export's additional delay is zero.

`ModelingDelay` is not an instruction to prepend that number of zeros to the original taps. The headphone path accounts for modeling delay in alignment. Native loader option `IRDataAttributes +17` can bake delay using a fixed five-sample stage for already-baked coefficients, or an 11-tap/128-phase sinc stage otherwise. The real-time headphone path also has its own delay processing. Those operations are not implicit parts of the on-disk record.

The static General/Movie reconstruction aligns room paths by 53/5 samples respectively and uses a 100-sample half-cosine overlap at early lengths 1536/1024. These are route-dependent processing steps, not changes to the stored IR. Source-extent fields `SourceExtentFilterDelay` and `SourceExtentSizeWeight` belong to SEIR processing; the mono InputChannel-indexed SEIR bank is not a binaural HRTF set.

## Triangulation: mixed endianness

Both HRIR files carry one mesh with 5680 triangles for 2842 records:

- `TriVertices[0]`: 68,160 bytes, triples of **big-endian 32-bit record indices**.
- `TriAssignment`: 11,368 bytes, one big-endian 32-bit mesh assignment per record; all zero here.
- `TriBinLengths[0]`: 8,192 bytes of big-endian 32-bit bin lengths.
- `TriBinSerial[0]`: packed big-endian 32-bit triangle indices for those bins.

The native loader byte-swaps all these integer streams. This does not change the little-endian encoding of audio records. Triangle interpolation uses spherical directions, inverse bases, containment tolerance, and normalized weights; merely applying independent linear azimuth/elevation interpolation loses the mesh behavior. The research player scans triangles instead of reproducing the native acceleration bins.

## Consolidated IRs and sound profiles

`extractIRDataTypePlist` reads `ImpulseResponses`, selects a matching Type and accumulates preceding entries' DataLengthBytes to find its payload. A requested Type of zero returns the outer dictionary directly. Therefore the ordinary single-record-bank formula must not be blindly applied to consolidated sound profiles. Native serialization and sound-profile methods exist; no consolidated original sample is included here, and the standalone Python IR reader explicitly rejects that container rather than misdecoding it.