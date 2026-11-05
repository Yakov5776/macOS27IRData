# Audio Unit presets and embedded binary data

Contains eight original presets. Adjacent research JSON files decode their entire plist and parameter streams. Python plistlib handles the plist encoding; the bytes inside a plist data value have their own encoding.

## Outer plist

The archived files are binary plists with numeric `type`, `subtype`, `manufacturer`, `version`, a `name`, and a binary `data` field. Integer FourCC values render as `aufx`/`aumx`, `scty`/`3dem`/`ldnm`/`cfrk`, and `appl` when converted to four big-endian bytes. An `.aupreset` extension alone does not require every AU to use this particular data schema.

## Parameter-group stream

All eight supplied `data` blobs can be consumed exactly as repeated groups:

```text
uint32_be scope
uint32_be element
uint32_be parameter_count
repeat parameter_count:
    uint32_be parameter_id
    float32_be value
```

IDs are scoped to a group; repeated IDs across elements are expected. The research Scotty and limiter loaders independently establish the 12-byte header and 8-byte ID/value entries; exact full-blob consumption establishes the additional group boundaries. Parameter names are component-specific, so the JSON uses numeric IDs rather than invented universal names.

| Component | Data bytes | Observed groups |
| --- | ---: | --- |
| Scotty, each category | 284 | scope 0, element 0, 34 parameters |
| Loudness normalizer | 380 | scope 0, element 0, 46 parameters |
| ControlFreak | 1596 | scope 0/element 0 with 9; scope 4/elements 0..17 with 9 each |
| 3D mixer, each preset | 8424 | scope 0/element 0 with 9; scope 1/elements 0..31 with 31 each; scope 2/element 0 with 1 |

The nine global limiter IDs map to its DSP metadata in the researched branch. IDs 3,4,5,6,7 are threshold dB, minimum fast gain dB, release milliseconds, true-peak enable, and lookahead milliseconds respectively. The local parser's restrictions are implementation scope, not a universal validity rule for all presets.

## Mixer properties are separate from AU parameters

`InputProperties` and `GlobalProperties` are arrays of dictionaries with decimal-string property IDs. `AUSMChannelOverrides` holds ChannelLabel, Azimuth, Elevation, Distance, Gain, Delay, and DRRAdjustment. Do not interpret property IDs as IDs in the binary parameter stream.

The researched route reads input property 3214 (late-send decorrelation), global 3265 (DRR), and 3108 (LFE low-pass frequency). All four mixer files have 3214=1 and 3108=150. General has 3265=13; Movie has 3265=3. Input property `3010` is a separate 12-byte **little-endian** float blob containing (1,1000,60); the byte interpretation is established, but this document does not assign unsupported field names.

General stereo front L/R angles are -49/+49 degrees and surrounds -130/+130. General multichannel uses -36/+36 and -110/+110. The General and Movie variants therefore cannot be selected solely by filename category while ignoring the input layout. Channel labels 4 and 37 are zero-distance LFE overrides in these presets.

## Routing evidence versus file content

The local AudioToolbox analysis resolves headphone presets under `/System/Library/Audio/Tunings/Generic/AU/`; more than two input channels selects multichannel, while Scotty is the stereo upmixer. The researched host dynamics chain is spatializer -> pre-gain -> normalizer -> limiter -> post-gain under its enabling conditions. A preset alone is not proof that a particular device/runtime route executes every stage.