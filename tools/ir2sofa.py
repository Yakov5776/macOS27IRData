"""Export the native coefficient bank to GeneralFIR, preserving all Apple axes.

This exports filters and additional delays, not the complete headphone renderer.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import sofar as sf
from apple_formats import IR, json_value

def export_sofa(filename, out_dir='sofa_output', scaling='renderer'):
    ir = IR(filename)
    records = [ir.record(i, scaling) for i in range(ir.count)]
    coords = np.asarray([r[0] for r in records])
    coeffs = np.asarray([r[1] for r in records])
    stored_delays = np.asarray([r[2] for r in records])
    positions = np.zeros((ir.count, 3))
    # Apple azimuth is positive right; SOFA azimuth is positive left.
    if 'Azimuth' in ir.axes:
        positions[:, 0] = (-coords[:, ir.axes.index('Azimuth')]) % 360
    if 'Elevation' in ir.axes:
        positions[:, 1] = coords[:, ir.axes.index('Elevation')]
    positions[:, 2] = coords[:, ir.axes.index('Distance')] if 'Distance' in ir.axes else 1
    sofa = sf.Sofa('GeneralFIR')
    sofa.Data_IR = coeffs
    sofa.Data_SamplingRate = ir.rate
    sofa.Data_Delay = np.zeros_like(stored_delays) if ir.user.get('DelayBakedInCoeffs', 0) else stored_delays
    sofa.SourcePosition = positions
    sofa.SourcePosition_Type = 'spherical'
    sofa.SourcePosition_Units = 'degree, degree, metre'
    sofa.ReceiverPosition = np.zeros((ir.channels, 3))
    sofa.GLOBAL_Title = ir.path.stem + ' native coefficient bank'
    sofa.GLOBAL_RoomType = 'reverberant' if ir.path.name.startswith(('BRIR_', 'Reverb_')) else 'free field'
    if sofa.GLOBAL_RoomType == 'reverberant':
        sofa.add_attribute('GLOBAL_RoomDescription', 'Apple room-processing filter bank; physical room dimensions not encoded in the asset.')
    sofa.GLOBAL_Organization = 'macOS27IRData research archive'
    sofa.GLOBAL_AuthorContact = 'Not supplied with the original asset'
    sofa.GLOBAL_Origin = ir.path.name
    sofa.GLOBAL_References = 'SPEC.md'
    sofa.GLOBAL_Comment = ('Virtual filter-bank representation. Source distance 1 is a unit-direction reference when absent; '
        'receiver coordinates are reference origins, not measured ear positions. Original axis values are in AppleCoordinates. '
        'No room windows, polyphase delay filter, resampling, host gain or dynamics are baked into Data.IR.')
    sofa.add_attribute('GLOBAL_AppleScaling', scaling)
    sofa.add_attribute('GLOBAL_AppleSourceSHA256', hashlib.sha256(ir.raw).hexdigest())
    sofa.add_attribute('GLOBAL_AppleMetadataJSON', json.dumps(json_value(ir.metadata)))
    sofa.add_attribute('GLOBAL_AppleAxisNames', json.dumps(ir.axes))
    sofa.add_variable('AppleCoordinates', coords, 'double', 'MD')
    sofa.add_variable('AppleStoredDelay', stored_delays, 'double', 'MR')
    sofa.add_attribute('AppleStoredDelay_Units', 'sample')
    sofa.verify()
    out = Path(out_dir)/f'{ir.path.stem}.sofa'
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write_sofa(str(out), sofa)
    # Read back through an independent container parser and verify every record.
    from netCDF4 import Dataset
    with Dataset(out) as loaded:
        np.testing.assert_array_equal(loaded['Data.IR'][:], coeffs)
        np.testing.assert_array_equal(loaded['Data.Delay'][:], sofa.Data_Delay)
        np.testing.assert_array_equal(loaded['AppleCoordinates'][:], coords)
        np.testing.assert_array_equal(loaded['AppleStoredDelay'][:], stored_delays)
        np.testing.assert_array_equal(loaded['SourcePosition'][:], positions)
    print(f'Validated {out}: {ir.count} records, {ir.channels} channels, {scaling} scaling')
    return out

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file')
    p.add_argument('out_dir', nargs='?', default='sofa_output')
    p.add_argument('--scaling', choices=['stored','renderer'], default='renderer')
    a = p.parse_args()
    export_sofa(a.file, a.out_dir, a.scaling)
