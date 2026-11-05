import json
from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from apple_formats import IR, parameter_groups
from ir2wav import export_wav

class Formats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'fixture.ir'

    def fixture(self, fmt='int16', delays=True, **metadata):
        d = dict(NumChannels=2, FilterLength=2, TotalNumCoordinates=1,
                 SampleRate=48000, Dimensions=[dict(Name='Azimuth')],
                 CoefficientFormat=fmt, FilterScaleFactor=.5,
                 UserData=dict(DiffuseFieldPowerRMS=2))
        if delays:
            d['DelayFormat'] = 'float32'
        d.update(metadata)
        p = plistlib.dumps(d, fmt=plistlib.FMT_BINARY)
        body = struct.pack('<f',90)
        for taps, delay in [((2,-4),1.25),((6,-8),2.5)]:
            body += struct.pack('<2'+('h' if fmt=='int16' else 'f'), *taps)
            if delays:
                body += struct.pack('<f',delay)
        self.path.write_bytes(struct.pack('<I',len(p))+p+body)
        return IR(self.path)

    def test_channel_order_and_scaling(self):
        ir = self.fixture()
        self.assertEqual(ir.record(0,'raw'), ((90,),[(2,-4),(6,-8)],[1.25,2.5]))
        self.assertEqual(ir.record(0,'renderer')[1],[(.5,-1),(1.5,-2)])

    def test_float_scaling_and_absent_delays(self):
        ir = self.fixture('float32',False)
        self.assertEqual(ir.record(0)[1],[(1,-2),(3,-4)])
        self.assertEqual(ir.record(0)[2],[0,0])

    def test_bounds_and_unknown_format(self):
        ir = self.fixture()
        for i in [-1,1]:
            with self.assertRaises(ValueError):ir.record(i)
        original = self.path.read_bytes()
        for b in [b'', original[:-1], original+b'X', b'\xff'*4+original[4:]]:
            self.path.write_bytes(b)
            with self.assertRaises(ValueError):IR(self.path)
        with self.assertRaises(ValueError):self.fixture(CoefficientFormat='int24')
        with self.assertRaises(ValueError):self.fixture(DelayFormat='float64')

    def test_rms_threshold(self):
        ir = self.fixture(UserData=dict(DiffuseFieldPowerRMS=2**-23))
        self.assertEqual(ir.record(0,'renderer')[1],ir.record(0,'stored')[1])

    def test_parameter_groups_and_errors(self):
        b = struct.pack('>IIIIf',0,0,1,7,1.5)+struct.pack('>IIIIf',1,3,1,7,2.5)
        groups = parameter_groups(b)
        self.assertEqual(groups[1],dict(scope=1,element=3,parameters={7:2.5}))
        for bad in [b[:-1],b+b'X',struct.pack('>IIIIfIf',0,0,2,1,0,1,1),
                    struct.pack('>IIIIf',0,0,1,1,float('nan'))]:
            with self.assertRaises(ValueError):parameter_groups(bad)

    def test_wav_unclipped_float_and_sidecar(self):
        self.fixture()
        export_wav(self.path,self.tmp.name)
        target = Path(self.tmp.name)/'fixture'
        b = (target/'fixture_0000.wav').read_bytes()
        self.assertEqual(struct.unpack_from('<H',b,20)[0],3)
        pos = b.index(b'data')+8
        self.assertEqual(struct.unpack_from('<4f',b,pos),(1,3,-2,-4))
        side = json.loads((target/'metadata.json').read_text())
        self.assertFalse(side['delays_applied'])
        self.assertEqual(side['records'][0]['stored_delays_samples'],[1.25,2.5])

if __name__ == '__main__':unittest.main()
