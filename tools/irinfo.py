import argparse, json
from apple_formats import IR, json_value
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Validated IR metadata; blobs as hex.')
    p.add_argument('files', nargs='+')
    for path in p.parse_args().files:
        ir = IR(path)
        print(json.dumps(dict(file=path, bytes=len(ir.raw), payload_offset=ir.offset,
            record_bytes=ir.stride, metadata=json_value(ir.metadata)), indent=2))
