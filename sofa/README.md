# SOFA coefficient banks

All eleven files are generated from the original IRs with `tools/ir2sofa.py` using an IDA-verified mapping. They use GeneralFIR, SOFA azimuth handedness, renderer coefficient scaling, additional delays, and custom AppleCoordinates/AppleStoredDelay fields.

These preserve filter banks, not a complete spatial renderer or a fabricated physical measurement setup. Consumers of SEIR must retain its InputChannel coordinate. The original metadata and source SHA-256 are embedded. Regenerate from the repository root with:

```powershell
Get-ChildItem *.ir | ForEach-Object { py tools/ir2sofa.py $_.FullName sofa }
```
