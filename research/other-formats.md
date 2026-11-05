# Related binary formats in the research project

This archive now includes AU presets and the extracted Scotty table package in addition to IRs. Other researched streams are indexed here without confusing them with interchangeable IR file types.

## SCTYTB01 (included)

`tables/scotty-tables.bin` is a **project-defined** extraction wrapper:

| Offset | Bytes | Contents |
| ---: | ---: | --- |
| 0 | 8 | ASCII SCTYTB01 |
| 8 | 29,484 | 81 x 91 little-endian float32 front steering table |
| 29,492 | 29,484 | 81 x 91 little-endian float32 surround steering table |
| 58,976 | 24 | Six little-endian uint32 allpass delays: 105,116,17,117,81,13 |
