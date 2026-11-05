import argparse, json
from apple_formats import IR
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Inspect IR coefficients without baking delays.')
    p.add_argument('file')
    p.add_argument('index', type=int, nargs='?', default=0)
    p.add_argument('--scaling', choices=['raw','stored','renderer'], default='raw')
    a = p.parse_args()
    ir = IR(a.file)
    coords, coeffs, delays = ir.record(a.index, a.scaling)
    print(json.dumps(dict(coordinates=dict(zip(ir.axes, coords)), stored_delays_samples=delays,
        delay_baked=bool(ir.user.get('DelayBakedInCoeffs', 0)), scaling=a.scaling,
        first_ten_coefficients=[c[:10] for c in coeffs]), indent=2))
