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
        
        # Each record layout:
        # [Coordinates: num_dims * 4 bytes]
        # Followed by each channel's block:
        #   [Coefficients: filter_length * coeff_format_size]
        #   [Delay: delay_format_size (float32, 4 bytes)]
        chan_data_size = filter_length * coeff_format_size + delay_format_size
        record_size = num_dims * coord_format_size + num_channels * chan_data_size
        
        if record_index >= total_coords:
            print(f"Error: record index {record_index} out of bounds (max {total_coords - 1})")
            return
            
        payload_offset = 4 + length
        f.seek(payload_offset + record_index * record_size)
        
        record = f.read(record_size)
        
        coord_bytes = record[0 : num_dims * 4]
        coords = struct.unpack(f'<{num_dims}f', coord_bytes)
        
        delays = []
        coeffs = []
        offset = num_dims * 4
        chan_coeff_bytes = filter_length * coeff_format_size
        
        for c in range(num_channels):
            c_bytes = record[offset : offset + chan_coeff_bytes]
            offset += chan_coeff_bytes
            if is_int16:
                c_data = struct.unpack(f'<{filter_length}h', c_bytes)
            else:
                c_data = struct.unpack(f'<{filter_length}f', c_bytes)
            coeffs.append(c_data)
            
            if delay_format_size > 0:
                d_val = struct.unpack('<f', record[offset : offset + delay_format_size])[0]
                delays.append(d_val)
                offset += delay_format_size
            else:
                delays.append(0.0)
            
        print(f"=== Record {record_index} of {filename} ===")
        print(f"Coordinates ({[d.get('Name') for d in pl.get('Dimensions', [])]}): {coords}")
        print(f"Delays: {delays}")
        print("Coefficients:")
        for c in range(num_channels):
            print(f"  Channel {c} (first 10): {coeffs[c][:10]}")
            
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.ir> [record_index]")
        sys.exit(1)
        
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    dump_ir(sys.argv[1], idx)
