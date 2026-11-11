"""Verify local inference artifacts against the recorded source snapshot."""
import argparse,hashlib,json,pathlib,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--root',type=pathlib.Path,required=True)
a=p.parse_args()
manifest=json.loads((pathlib.Path(__file__).resolve().parents[1]/'docs/model-manifest.json').read_text(encoding='utf-8'))
bad=0;checked=0
for model in manifest['models']:
    for entry in model['files']:
        f=a.root/model['runtime_path']/entry['path']
        ok=f.is_file() and f.stat().st_size==entry['bytes']
        if ok:
            h=hashlib.sha256()
            with f.open('rb') as stream:
                for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
            ok=h.hexdigest()==entry['sha256']
        checked+=1
        if not ok:bad+=1;print('MISSING OR MISMATCH:',f)
print(f'Checked {checked} files; failures: {bad}')
sys.exit(1 if bad else 0)
