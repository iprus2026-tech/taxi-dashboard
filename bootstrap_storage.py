#!/usr/bin/env python3
"""Controlled bootstrap for an existing Taxi Dashboard JSON store.

Dry-run is the default.  No file is written unless --apply and --confirm are
both supplied.  A blocked storage requires --recover-block as well.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from storage import StorageFailure, StorageManager


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--recover-block", action="store_true")
    args = parser.parse_args()

    manager = StorageManager(args.base_dir)
    try:
        plan = manager.bootstrap_plan()
    except StorageFailure as exc:
        print(f"BOOTSTRAP BLOCKED: {exc.code}")
        return 1

    print("BOOTSTRAP PLAN")
    print(f"block_present={plan['block_present']}")
    print(f"meta_present={plan['meta_present']}")
    print(f"state_present={plan['state_present']}")
    print(f"history_present={plan['history_present']}")
    print(f"valid={plan['valid']}")

    if not args.apply:
        print("DRY RUN: no changes")
        return 0
    if not args.confirm:
        print("REFUSED: --apply requires --confirm")
        return 2
    if plan["block_present"] and not args.recover_block:
        print("REFUSED: block-marker present; use --recover-block only after backup")
        return 2
    if not plan["valid"]:
        print("REFUSED: storage is not valid; no changes")
        return 1

    try:
        meta = manager.bootstrap_existing(recover_block=args.recover_block)
    except StorageFailure as exc:
        print(f"BOOTSTRAP FAILED: {exc.code}")
        return 1

    print("BOOTSTRAP OK")
    print(f"schema_version={meta['schema_version']}")
    print(f"state_initialized={meta['state_initialized']}")
    print(f"history_initialized={meta['history_initialized']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
