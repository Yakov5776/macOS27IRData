"""Export float WAV coefficient arrays plus timing/coordinate sidecar."""
import argparse, json, struct
from pathlib import Path
from apple_formats import IR, json_value

def export_wav(filename, out_dir='wav_output', scaling='stored'):
    ir = IR(filename)
    if ir.rate != int(ir.rate):
        raise ValueError('WAV requires integral sample rate')
    target = Path(out_dir)/ir.path.stem
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for i in range(ir.count):
        coords, coeffs, delays = ir.record(i, scaling)
        samples = [v for frame in zip(*coeffs) for v in frame]
        data = struct.pack('<'+str(len(samples))+'f', *samples)
        fmt = struct.pack('<HHIIHH', 3, ir.channels, int(ir.rate), int(ir.rate)*ir.channels*4, ir.channels*4, 32)
        chunks = b'fmt '+struct.pack('<I', len(fmt))+fmt
        chunks += b'fact'+struct.pack('<II', 4, ir.length)
        chunks += b'data'+struct.pack('<I', len(data))+data
        name = f'{ir.path.stem}_{i:04d}.wav'
        (target/name).write_bytes(b'RIFF'+struct.pack('<I', len(chunks)+4)+b'WAVE'+chunks)
        records.append(dict(file=name, coordinates=coords, stored_delays_samples=delays))
    sidecar = dict(source=ir.path.name, scaling=scaling, delays_applied=False,
        note='Coefficient arrays only; no interpolation, fractional-delay filter, room windows or host DSP.',
        metadata=json_value(ir.metadata), records=records)
    (target/'metadata.json').write_text(json.dumps(sidecar, indent=2)+'\n', encoding='utf-8')
    print(f'Exported {ir.count} float WAVs and metadata.json to {target}')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file')
    p.add_argument('out_dir', nargs='?', default='wav_output')
    p.add_argument('--scaling', choices=['stored','renderer'], default='stored')
    a = p.parse_args()
    export_wav(a.file, a.out_dir, a.scaling)
