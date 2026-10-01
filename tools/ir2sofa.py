#!/usr/bin/env python3
import struct
import plistlib
import sys
import os
import datetime

try:
    from netCDF4 import Dataset
    import numpy as np
except ImportError:
    print("Error: 'netCDF4' and 'numpy' libraries are required to create SOFA files.")
    print("Please install them by running: pip install netCDF4 numpy")
    sys.exit(1)

def export_sofa(filename, out_dir="."):
    with open(filename, 'rb') as f:
        hdr = f.read(4)
        length = struct.unpack('<I', hdr)[0]
        pl = plistlib.loads(f.read(length))
        
        num_dims = len(pl.get('Dimensions', []))
        num_channels = pl.get('NumChannels', 1)
        filter_length = pl.get('FilterLength', 0)
        total_coords = pl.get('TotalNumCoordinates', 1)
        scale_factor = pl.get('FilterScaleFactor', 1.0)
        sample_rate = float(pl.get('SampleRate', 48000.0))
        
        coord_format_size = 4
        delay_format_size = 4 if pl.get('DelayFormat') == 'float32' else 0
        is_int16 = (pl.get('CoefficientFormat') == 'int16')
        coeff_format_size = 2 if is_int16 else 4
        
        record_size = num_dims * coord_format_size + num_channels * delay_format_size + num_channels * filter_length * coeff_format_size
        
        payload_offset = 4 + length
        f.seek(payload_offset)
        
        ir_data = np.zeros((total_coords, num_channels, filter_length), dtype=np.float64)
        source_positions = np.zeros((total_coords, 3), dtype=np.float64)
        delays = np.zeros((total_coords, num_channels), dtype=np.float64)
        
        dim_names = [d.get('Name', '').lower() for d in pl.get('Dimensions', [])]
        az_idx = dim_names.index('azimuth') if 'azimuth' in dim_names else -1
        el_idx = dim_names.index('elevation') if 'elevation' in dim_names else -1
        
        for i in range(total_coords):
            record = f.read(record_size)
            if len(record) < record_size:
                break
                
            coord_bytes = record[0 : num_dims*4]
            coords = struct.unpack(f'<{num_dims}f', coord_bytes)
            
            az = coords[az_idx] if az_idx != -1 else 0.0
            el = coords[el_idx] if el_idx != -1 else 0.0
            r = 1.0 
            
            # SOFA typical azimuth is 0..360
            if az < 0:
                az += 360.0
                
            source_positions[i] = [az, el, r]
            
            delay_offset = num_dims * 4
            delay_bytes = record[delay_offset : delay_offset + num_channels * delay_format_size]
            if delay_format_size > 0:
                delays[i] = struct.unpack(f'<{num_channels}f', delay_bytes)
                
            coeff_offset = delay_offset + num_channels * delay_format_size
            coeff_bytes = record[coeff_offset:]
            
            if is_int16:
                coeffs = struct.unpack(f'<{num_channels * filter_length}h', coeff_bytes)
            else:
                coeffs = struct.unpack(f'<{num_channels * filter_length}f', coeff_bytes)
            
            c_array = np.array(coeffs, dtype=np.float64).reshape((num_channels, filter_length))
            c_array *= scale_factor
            ir_data[i] = c_array
            
        base_name = os.path.splitext(os.path.basename(filename))[0]
        out_path = os.path.join(out_dir, f"{base_name}.sofa")
        os.makedirs(out_dir, exist_ok=True)
        
        print(f"Creating SOFA file: {out_path}...")
        
        root = Dataset(out_path, 'w', format='NETCDF4')
        
        # Global Attributes mapping to standard SOFA specifications
        root.Conventions = "SOFA"
        root.Version = "2.1"
        root.SOFAConventions = "SimpleFreeFieldHRIR"
        root.SOFAConventionsVersion = "1.0"
        root.APIName = "Apple IR to SOFA Converter"
        root.APIVersion = "1.0"
        root.AuthorContact = "Apple"
        root.Organization = "Custom"
        root.License = "No license provided"
        root.DataType = "FIR"
        root.RoomType = "free field"
        root.Title = pl.get('Description', base_name)
        root.DateCreated = datetime.datetime.utcnow().isoformat() + 'Z'
        root.DateModified = root.DateCreated
        root.DatabaseName = "Apple Spatial Audio IRs"
        root.ListenerShortName = "Apple Head"
        
        # Dimensions
        root.createDimension("M", total_coords)  # Measurements
        root.createDimension("N", filter_length) # Samples
        root.createDimension("R", num_channels)  # Receivers
        root.createDimension("E", 1)             # Emitters
        root.createDimension("I", 1)             # Singleton
        root.createDimension("C", 3)             # Coordinates
        
        # Variables
        v_sr = root.createVariable("Data.SamplingRate", "f8", ("I",))
        v_sr.Units = "hertz"
        v_sr[:] = [sample_rate]
        
        v_del = root.createVariable("Data.Delay", "f8", ("M", "R"))
        v_del[:] = delays
        
        v_ir = root.createVariable("Data.IR", "f8", ("M", "R", "N"))
        v_ir[:] = ir_data
        
        v_lp = root.createVariable("ListenerPosition", "f8", ("I", "C"))
        v_lp.Type = "cartesian"
        v_lp.Units = "meter"
        v_lp[:] = [[0.0, 0.0, 0.0]]
        
        v_lv = root.createVariable("ListenerView", "f8", ("I", "C"))
        v_lv.Type = "cartesian"
        v_lv.Units = "meter"
        v_lv[:] = [[1.0, 0.0, 0.0]] 
        
        v_lu = root.createVariable("ListenerUp", "f8", ("I", "C"))
        v_lu.Type = "cartesian"
        v_lu.Units = "meter"
        v_lu[:] = [[0.0, 0.0, 1.0]]
        
        v_rp = root.createVariable("ReceiverPosition", "f8", ("R", "C", "I"))
        v_rp.Type = "cartesian"
        v_rp.Units = "meter"
        if num_channels == 2:
            v_rp[:] = [[[0.0], [0.09], [0.0]], [[0.0], [-0.09], [0.0]]]
        else:
            v_rp[:] = [[[0.0], [0.0], [0.0]]]
            
        v_sp = root.createVariable("SourcePosition", "f8", ("M", "C"))
        v_sp.Type = "spherical"
        v_sp.Units = "degree, degree, meter"
        v_sp[:] = source_positions
        
        v_ep = root.createVariable("EmitterPosition", "f8", ("E", "C", "I"))
        v_ep.Type = "cartesian"
        v_ep.Units = "meter"
        v_ep[:] = [[[0.0], [0.0], [0.0]]]
        
        root.close()
        print(f"Successfully built fully-compliant SOFA file: {out_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.ir> [out_dir]")
        sys.exit(1)
        
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "sofa_output"
    export_sofa(sys.argv[1], out_dir)
