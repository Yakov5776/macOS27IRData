#!/usr/bin/env python3
import struct
import plistlib
import sys
import os
import wave

def export_wav(filename, out_dir="."):
    with open(filename, 'rb') as f:
        hdr = f.read(4)
        length = struct.unpack('<I', hdr)[0]
        pl = plistlib.loads(f.read(length))
        
        num_dims = len(pl.get('Dimensions', []))
        num_channels = pl.get('NumChannels', 1)
        filter_length = pl.get('FilterLength', 0)
        total_coords = pl.get('TotalNumCoordinates', 1)
        scale_factor = pl.get('FilterScaleFactor', 1.0)
        sample_rate = int(pl.get('SampleRate', 48000))
        
        coord_format_size = 4
        delay_format_size = 4 if pl.get('DelayFormat') == 'float32' else 0
        is_int16 = (pl.get('CoefficientFormat') == 'int16')
        coeff_format_size = 2 if is_int16 else 4
        
        record_size = num_dims * coord_format_size + num_channels * delay_format_size + num_channels * filter_length * coeff_format_size
        
        # Read the payload
        payload_offset = 4 + length
        f.seek(payload_offset)
        
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Create a subfolder if there are many records
        if total_coords > 1:
            out_dir = os.path.join(out_dir, base_name)
        os.makedirs(out_dir, exist_ok=True)
        
        print(f"Exporting {total_coords} IRs from {filename} to {out_dir}/ ...")
        
        for i in range(total_coords):
            record = f.read(record_size)
            if len(record) < record_size:
                break
                
            coord_bytes = record[0 : num_dims*4]
            coords = struct.unpack(f'<{num_dims}f', coord_bytes)
            
            coeff_offset = num_dims * 4 + num_channels * delay_format_size
            coeff_bytes = record[coeff_offset:]
            
            if is_int16:
                coeffs = struct.unpack(f'<{num_channels * filter_length}h', coeff_bytes)
            else:
                coeffs = struct.unpack(f'<{num_channels * filter_length}f', coeff_bytes)
            
            # The format is planar: [C0_0, C0_1 ... C0_N], [C1_0, C1_1 ... C1_N]
            # WAV expects interleaved: [C0_0, C1_0, C0_1, C1_1 ...]
            interleaved = []
            for s in range(filter_length):
                for c in range(num_channels):
                    val = coeffs[c * filter_length + s]
                    if is_int16:
                        # Convert to float and apply scale factor
                        f_val = val * scale_factor
                        f_val = max(min(f_val, 1.0), -1.0)
                        interleaved.append(int(f_val * 32767.0))
                    else:
                        f_val = max(min(val, 1.0), -1.0)
                        interleaved.append(int(f_val * 32767.0))
            
            # Pack interleaved data
            wav_data = struct.pack(f'<{len(interleaved)}h', *interleaved)
            
            coord_str = "_".join(f"{c:g}" for c in coords)
            if coord_str:
                out_name = f"{base_name}_{i:04d}_coords_{coord_str}.wav"
            else:
                out_name = f"{base_name}_{i:04d}.wav"
                
            out_path = os.path.join(out_dir, out_name)
            
            with wave.open(out_path, 'wb') as w:
                w.setnchannels(num_channels)
                w.setsampwidth(2) # 16-bit
                w.setframerate(sample_rate)
                w.writeframes(wav_data)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.ir> [out_dir]")
        sys.exit(1)
        
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "wav_output"
    export_wav(sys.argv[1], out_dir)
