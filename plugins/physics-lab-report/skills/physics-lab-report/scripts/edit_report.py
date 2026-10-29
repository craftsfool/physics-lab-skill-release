#!/usr/bin/env python3
"""Apply a uniquely located, revision-checked LaTeX edit without touching any other bytes."""
import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path


def apply_edit(source, edit, dry_run=False):
    source = Path(source)
    if source.is_symlink() or source.suffix != '.tex' or not source.is_file():
        raise ValueError('Choose an existing regular .tex source.')
    required = {'source_sha256', 'old_text', 'new_text'}
    if not isinstance(edit, dict) or not required <= edit.keys() or set(edit) - (required | {'start_line', 'end_line'}):
        raise ValueError('Expected source_sha256, old_text, new_text and optional inclusive line range.')
    original = source.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if not isinstance(edit['source_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', edit['source_sha256']):
        raise ValueError('A SHA256 of the selected source revision is required.')
    if digest != edit['source_sha256']:
        raise ValueError('Stale selection: re-read the current source and locate the selection again.')
    old, new = edit['old_text'], edit['new_text']
    if not isinstance(old, str) or not old or not isinstance(new, str):
        raise ValueError('Selection text must be nonempty; replacement must be text.')
    # Retain CRLF and every byte outside the selected UTF-8 text.
    text = original.decode('utf-8')
    begin, end = 0, len(text)
    if 'start_line' in edit or 'end_line' in edit:
        start, stop = edit.get('start_line'), edit.get('end_line')
        lines = text.splitlines(keepends=True)
        if type(start) is not int or type(stop) is not int or not 1 <= start <= stop <= len(lines):
            raise ValueError('A valid inclusive source line range is required.')
        begin = sum(map(len, lines[:start-1]))
        end = sum(map(len, lines[:stop]))
    area = text[begin:end]
    positions = [m.start() for m in re.finditer('(?=' + re.escape(old) + ')', area)]
    if len(positions) != 1:
        raise ValueError('Selection is absent or ambiguous; provide a current source range or clearer quotation.')
    start = begin + positions[0]
    result = (text[:start] + new + text[start+len(old):]).encode('utf-8')
    report = {'changed': result != original, 'dry_run': dry_run,
              'source_sha256': digest, 'updated_sha256': hashlib.sha256(result).hexdigest(),
              'compile_required': result != original, 'visual_review_required': result != original}
    if dry_run or result == original:
        return report
    fd, temporary = tempfile.mkstemp(prefix='.' + source.name + '-', dir=source.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(result)
        os.chmod(temporary, stat.S_IMODE(source.stat().st_mode))
        if source.is_symlink() or source.read_bytes() != original:
            raise ValueError('Source changed during edit; locate the selection again.')
        os.replace(temporary, source)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--edit', type=Path, required=True, help='UTF-8 JSON edit specification; not an API response.')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(apply_edit(args.source, json.loads(args.edit.read_text(encoding='utf-8')), args.dry_run)))
    except (OSError, ValueError) as error:
        parser.exit(1, 'Report not edited: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
