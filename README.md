# macOS 27 audio tuning data

Research archive of Apple IR filter banks and Audio Unit presets, documented using IDA analysis of AudioDSP/libAudioDSPCore.

## Contents

- Eleven original `.ir` files.
- `presets/`: eight original binary-plist `.aupreset` files: General/Movie Scotty stereo, General/Movie 3D mixer stereo and multichannel, loudness normalizer, and ControlFreak limiter.
- `tables/scotty-tables.bin`: the research project's **derived** SCTYTB01 wrapper around extracted ARM64 steering tables; not an Apple on-disk format.
- `sofa/`: eleven validated GeneralFIR coefficient banks with SOFA azimuth coordinates, explicit scaling and delays, and preserved Apple axes and metadata.
- `research/`: decoded preset JSON, IR inventory, provenance, and documentation.

Read [SPEC.md](SPEC.md), [AU preset formats](research/aupreset.md), [other binary formats](research/other-formats.md), and the [IR inventory](research/ir-inventory.md).

## Tools

```powershell
py tools/irdump.py HRIR_Movie.ir 0 --scaling renderer
py tools/irinfo.py BRIR_FT.ir
py tools/presetinfo.py presets/aufx-ldnm-appl-headphone.aupreset
py tools/ir2wav.py HRIR_Movie.ir wav_output --scaling renderer
py -m pip install -r tools/requirements-sofa.txt
py tools/ir2sofa.py HRIR_Movie.ir sofa_output
py -m unittest discover -s tests -v
py tools/verify_archive.py
py tools/verify_archive.py --sofa
```

`ir2wav` writes unclipped IEEE float32 coefficient WAVs plus a metadata/delay sidecar. Fractional delays are preserved in the metadata sidecar. `stored` scaling applies FilterScaleFactor; `renderer` additionally applies the recovered diffuse-field normalization. Neither export is a complete Apple renderer.

The SOFA files represent virtual filter banks with unit-direction source positions and co-located reference receivers. GeneralFIR permits this general representation. SEIR's InputChannel stays in `AppleCoordinates`; consumers must use it to distinguish records with the same direction. These are not measured SimpleFreeFieldHRIR datasets, and generic HRTF players may not understand SEIR.

Original assets are preserved for research and archival purposes; this repository does not assign a new license to Apple's resources. The portable reconstruction and native traces establish specific branches, not whole-system acoustic equivalence.
