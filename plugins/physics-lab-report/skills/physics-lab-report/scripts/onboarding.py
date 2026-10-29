#!/usr/bin/env python3
"""Remember introduction and reference choice; never store credentials or create project folders."""
import argparse
import json
import os
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MODES = ('device', 'api', 'local', 'none')


def default_path():
    if platform.system() == 'Windows':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming'))
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return base / 'physics-lab-report' / 'onboarding.json'


def read_state(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('State file cannot be a symbolic link.')
    if not path.exists():
        return {'schema_version': 1, 'introduced_at': None, 'reference_mode': None}
    value = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'introduced_at', 'reference_mode'}
            or value['schema_version'] != 1
            or value['reference_mode'] not in (*MODES, None)
            or not isinstance(value['introduced_at'], (str, type(None)))):
        raise ValueError('Invalid onboarding state; do not infer reference authorization.')
    return value


def update(path, action, reference_mode=None):
    path = Path(path)
    state = read_state(path) if action != 'reset' else {
        'schema_version': 1, 'introduced_at': None, 'reference_mode': None}
    if path.is_symlink():
        raise ValueError('State file cannot be a symbolic link.')
    if action == 'status':
        return {**state, 'needs_introduction': state['introduced_at'] is None}
    if action == 'introduced':
        state['introduced_at'] = state['introduced_at'] or datetime.now(timezone.utc).isoformat()
    elif action == 'choose-source':
        if reference_mode not in MODES:
            raise ValueError('Choose device, api, local or none explicitly.')
        state['reference_mode'] = reference_mode
    elif action != 'reset':
        raise ValueError('Unknown state action.')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.onboarding-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(state, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {**state, 'needs_introduction': state['introduced_at'] is None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'introduced', 'choose-source', 'reset'])
    parser.add_argument('--state-file', type=Path, default=default_path())
    parser.add_argument('--reference-mode', choices=MODES)
    args = parser.parse_args()
    try:
        print(json.dumps(update(args.state_file, args.action, args.reference_mode), ensure_ascii=False))
    except (OSError, ValueError) as error:
        parser.exit(1, 'Onboarding state unavailable; use conversation context: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
