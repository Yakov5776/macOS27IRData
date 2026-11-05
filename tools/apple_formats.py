"""Readers for the archived samples; see SPEC.md for scope."""
import math
from pathlib import Path
import plistlib
import struct

class IR:
    def __init__(self, path):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        if len(self.raw) < 12:
            raise ValueError('truncated IR header')
        n, = struct.unpack_from('<I', self.raw)
        if n > len(self.raw)-4 or self.raw[4:12] != b'bplist00':
            raise ValueError('invalid metadata extent/signature')
        self.metadata = d = plistlib.loads(self.raw[4:4+n])
        if not isinstance(d, dict) or 'ImpulseResponses' in d:
            raise ValueError('unsupported IR container')
        for key in ('NumChannels', 'FilterLength', 'TotalNumCoordinates'):
            if type(d.get(key)) is not int or d[key] <= 0:
                raise ValueError('invalid ' + key)
        self.channels, self.length, self.count = (d[k] for k in
            ('NumChannels', 'FilterLength', 'TotalNumCoordinates'))
        self.axes = [axis['Name'] for axis in d['Dimensions']]
        formats = {'int16': ('h', 2), 'float32': ('f', 4)}
        if d.get('CoefficientFormat') not in formats:
            raise ValueError('unsupported coefficient format')
        self.code, width = formats[d['CoefficientFormat']]
        self.has_delay = 'DelayFormat' in d
        if self.has_delay and d['DelayFormat'] != 'float32':
            raise ValueError('unsupported delay format')
        self.stride = 4*len(self.axes)+self.channels*(self.length*width+4*self.has_delay)
        self.offset = 4+n
        if self.offset+self.count*self.stride != len(self.raw):
            raise ValueError('IR payload length mismatch')
        self.scale = float(d.get('FilterScaleFactor', 1))
        self.rate = float(d['SampleRate'])
        self.user = d.get('UserData', {})
        self.rms = float(self.user.get('DiffuseFieldPowerRMS', 1))
        if not all(map(math.isfinite, (self.scale, self.rate, self.rms))) or self.rate <= 0:
            raise ValueError('invalid scale/rate/RMS')

    def record(self, index, scaling='stored'):
        if not 0 <= index < self.count:
            raise ValueError('record index out of bounds')
        if scaling not in ('raw', 'stored', 'renderer'):
            raise ValueError('unknown scaling policy')
        scale = 1 if scaling == 'raw' else self.scale
        if scaling == 'renderer' and abs(self.rms) > 2**-23:
            scale /= self.rms
        pos = self.offset+index*self.stride
        coords = struct.unpack_from('<'+'f'*len(self.axes), self.raw, pos)
        pos += len(self.axes)*4
        coeffs, delays = [], []
        fmt = '<'+str(self.length)+self.code
        for _ in range(self.channels):
            coeffs.append(tuple(v*scale for v in struct.unpack_from(fmt, self.raw, pos)))
            pos += struct.calcsize(fmt)
            delays.append(struct.unpack_from('<f', self.raw, pos)[0] if self.has_delay else 0)
            pos += 4*self.has_delay
        if not all(math.isfinite(v) for seq in (coords, delays, *coeffs) for v in seq):
            raise ValueError('nonfinite IR record')
        return coords, coeffs, delays

def parameter_groups(data):
    """Observed BE scope/element/count + (ID, float) groups, not all AU states."""
    groups, pos = [], 0
    while pos < len(data):
        if len(data)-pos < 12:
            raise ValueError('truncated AU header')
        scope, element, count = struct.unpack_from('>III', data, pos)
        pos += 12
        if count > (len(data)-pos)//8:
            raise ValueError('truncated AU parameters')
        params = {}
        for _ in range(count):
            key, value = struct.unpack_from('>If', data, pos)
            pos += 8
            if key in params or not math.isfinite(value):
                raise ValueError('duplicate/nonfinite AU parameter')
            params[key] = value
        groups.append(dict(scope=scope, element=element, parameters=params))
    return groups

def json_value(value):
    if isinstance(value, bytes):
        return {'byte_length': len(value), 'hex': value.hex()}
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value
