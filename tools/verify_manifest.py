#!/usr/bin/env python3
"""Verify all files recorded in the published artifact manifest."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'SHA256.json').read_text())
failures = []
for relative, expected in manifest.items():
    path = root / relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        failures.append(relative)
if failures:
    raise SystemExit('Missing or modified files:\n' + '\n'.join(failures))
print(f'Verified {len(manifest)} published files.')
