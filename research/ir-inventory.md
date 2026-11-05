# IR inventory

All are 48,000 Hz, int16 coefficients, float32 stored delays. Every record was decoded and checked for finite values; exact payload sizes match. Zero in the last two columns includes an absent metadata key.

| File | Records | Channels | Taps/channel | Axes in storage order | Baked delay | Modeling delay (samples) |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| BRIR_APAC_BCM.ir | 72 | 2 | 1536 | Azimuth | 1 | 0 |
| BRIR_FT.ir | 72 | 2 | 768 | Azimuth | 1 | 0 |
| BRIR_General_2026.ir | 72 | 2 | 1536 | Azimuth | 1 | 0 |
| BRIR_Movie_2026.ir | 72 | 2 | 1024 | Azimuth | 1 | 0 |
| HRIR_General.ir | 2842 | 2 | 128 | Elevation, Azimuth | 1 | 48 |
| HRIR_Movie.ir | 2842 | 2 | 64 | Elevation, Azimuth | 0 | 0 |
| Reverb_APAC_BCM.ir | 1 | 2 | 8192 | Azimuth | 1 | 0 |
| Reverb_FT.ir | 1 | 2 | 3072 | Azimuth | 1 | 0 |
| Reverb_General_2026.ir | 1 | 2 | 8192 | Azimuth | 1 | 0 |
| Reverb_Movie_2026.ir | 1 | 2 | 16384 | Azimuth | 1 | 0 |
| SEIR_APAC_BCM.ir | 380 | 1 | 1024 | Elevation, Azimuth, InputChannel | 0 | 0 |
