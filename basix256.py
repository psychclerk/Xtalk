#!/usr/bin/env python3
"""Backward-compatible shim for old Basix-256 entrypoint."""

from basic256 import main

if __name__ == "__main__":
    raise SystemExit(main())
