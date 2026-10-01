#!/usr/bin/env python3
import struct
import plistlib
import sys
import os

def dump_ir(filename, record_index=0):
    with open(filename, 'rb') as f:
        hdr = f.read(4)
        length = struct.unpack('<I', hdr)[0]
        pl = plistlib.loads(f.read(length))
        
        num_dims = len(pl.get('Dimensions', []))
        num_channels = pl.get('NumChannels', 1)
        filter_length = pl.get('FilterLength', 0)
        total_coords = pl.get('TotalNumCoordinates', 1)
        
        coord_format_size = 4
        delay_format_size = 4 if pl.get('DelayFormat') == 'float32' else 0
        is_int16 = (pl.get('CoefficientFormat') == 'int16')
        coeff_format_size = 2 if is_int16 else 4
        
        record_size = num_dims * coord_format_size + num_channels * delay_format_size + num_channels * filter_length * coeff_format_size
        
        if record_index >= total_coords:
            print(f"Error: record index {record_index} out of bounds (max {total_coords - 1})")
            return
            
        payload_offset = 4 + length
        f.seek(payload_offset + record_index * record_size)
        
        record = f.read(record_size)
        
        coord_bytes = record[0 : num_dims*4]
        coords = struct.unpack(f'<{num_dims}f', coord_bytes)
        
        delay_offset = num_dims * 4
        delay_bytes = record[delay_offset : delay_offset + num_channels * delay_format_size]
        if delay_format_size > 0:
            delays = struct.unpack(f'<{num_channels}f', delay_bytes)
        else:
            delays = []
            
        coeff_offset = delay_offset + num_channels * delay_format_size
        coeff_bytes = record[coeff_offset:]
        if is_int16:
            coeffs = struct.unpack(f'<{num_channels * filter_length}h', coeff_bytes)
        else:
            coeffs = struct.unpack(f'<{num_channels * filter_length}f', coeff_bytes)
            
        print(f"=== Record {record_index} of {filename} ===")
        print(f"Coordinates ({[d.get('Name') for d in pl.get('Dimensions', [])]}): {coords}")
        print(f"Delays: {delays}")
        print("Coefficients:")
        for c in range(num_channels):
            channel_coeffs = coeffs[c * filter_length : (c + 1) * filter_length]
            print(f"  Channel {c} (first 10): {channel_coeffs[:10]}")
            
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.ir> [record_index]")
        sys.exit(1)
        
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    dump_ir(sys.argv[1], idx)
