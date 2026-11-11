"""Download verified, version-pinned ModelScope artifacts, then check SHA256."""
import argparse
import hashlib
import json
import os
import pathlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=pathlib.Path)
    parser.add_argument('--model', action='append', help='Model name; repeat to select several')
    args = parser.parse_args()
    manifest = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'docs/model-manifest.json').read_text(encoding='utf-8'))
    models = manifest['models']
    if args.model:
        unknown = set(args.model) - {m['name'] for m in models}
        if unknown:
            parser.error('Unknown models: ' + ', '.join(sorted(unknown)))
        models = [m for m in models if m['name'] in args.model]
    pending = [m['name'] for m in models if m.get('upload_status') != 'verified' or not m.get('hosting_url') or not m.get('revision')]
    if pending:
        parser.error('Upload or remote verification is pending: ' + ', '.join(pending))
    from modelscope_hub import HubApi
    api = HubApi(token=os.environ.get('MODELSCOPE_API_TOKEN'))
    for model in models:
        target = args.root / model['runtime_path']
        api.download_repo(model['repo_id'], 'model', revision=model['revision'], local_dir=target, allow_patterns=[f['path'] for f in model['files']], max_workers=4)
        for entry in model['files']:
            file = target / entry['path']
            if not file.is_file() or file.stat().st_size != entry['bytes']:
                raise RuntimeError('Missing or incorrect size: ' + str(file))
            digest = hashlib.sha256()
            with file.open('rb') as stream:
                for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                    digest.update(chunk)
            if digest.hexdigest() != entry['sha256']:
                raise RuntimeError('SHA256 mismatch: ' + str(file))
        print('Verified:', model['name'])


if __name__ == '__main__':
    main()
