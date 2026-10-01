#!/usr/bin/env python3
import struct
import plistlib
import sys
import os

def print_info(filename):
    with open(filename, 'rb') as f:
        file_size = os.fstat(f.fileno()).st_size
        hdr = f.read(4)
        length = struct.unpack('<I', hdr)[0]
        pl = plistlib.loads(f.read(length))
        
        print(f"File:         {os.path.basename(filename)}")
        print(f"Format:       Apple IR")
        print(f"File size:    {file_size} bytes")
        print(f"Sample rate:  {pl.get('SampleRate')} Hz")
        print(f"Format:       {pl.get('CoefficientFormat')}")
        print(f"Channels:     {pl.get('NumChannels')}")
        print(f"Positions:    {pl.get('TotalNumCoordinates')}")
        print(f"Samples/IR:   {pl.get('FilterLength')}")
        print(f"Dimensions:   {[d.get('Name') for d in pl.get('Dimensions', [])]}")
        print(f"Description:  {pl.get('Description', '')}")
        print(f"Scale Factor: {pl.get('FilterScaleFactor')}")
        
        if 'UserData' in pl:
            print("User Data:")
            for k, v in pl['UserData'].items():
                print(f"  {k}: {v}")
        print("-" * 40)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.ir> ...")
        sys.exit(1)
    for arg in sys.argv[1:]:
        print_info(arg)
