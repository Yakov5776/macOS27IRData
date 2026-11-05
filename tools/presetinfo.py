import argparse, json, plistlib
from pathlib import Path
from apple_formats import parameter_groups, json_value
if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Inspect plist and observed AU parameter groups.')
    p.add_argument('files', nargs='+')
    for path in p.parse_args().files:
        d = plistlib.loads(Path(path).read_bytes())
        result = dict(file=path, plist=json_value(d))
        if isinstance(d.get('data'), bytes):
            result['parameter_groups'] = parameter_groups(d['data'])
        print(json.dumps(result, indent=2))
