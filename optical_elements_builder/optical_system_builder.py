#!/usr/bin/env python3
"""Inkscape effect entry point for the interactive optical-system builder."""
import argparse
import sys
from pathlib import Path

from optical_builder.model import SvgSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', action='append', default=[])
    parser.add_argument('--selected-nodes', action='append', default=[])
    parser.add_argument('svg', nargs='?')
    args = parser.parse_args()
    original = Path(args.svg).read_bytes() if args.svg else sys.stdin.buffer.read()
    try:
        session = SvgSession(original, args.id)
        from optical_builder.gui import Editor
        editor = Editor(session)
        result = session.result(editor.run())
    except Exception as error:
        # Returning no modified document prevents a partial effect being applied.
        print(f'Optical Elements: {error}', file=sys.stderr)
        return 1
    sys.stdout.buffer.write(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
