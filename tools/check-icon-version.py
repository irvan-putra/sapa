#!/usr/bin/env python3
import hashlib,json,re,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
v=re.search(r'versionName\s+"([^"]+)"',(root/'app/build.gradle').read_text()).group(1)
m=json.loads((root/'tools/icon-manifest.json').read_text())
assert m['version']==v, 'Icon manifest must be regenerated with the app version'
actual={str(p.relative_to(root)) for p in (root/'app/src/main/res').glob('drawable/ic_launcher.png')}
assert actual==set(m['sha256']), 'Launcher icon asset list changed'
for f,sha in m['sha256'].items():
    assert hashlib.sha256((root/f).read_bytes()).hexdigest()==sha, f+' differs from inspected versioned icon'
print('Verified all launcher icon hashes for '+v)
