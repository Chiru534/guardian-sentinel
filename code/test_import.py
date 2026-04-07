#!/usr/bin/env python
"""Debug script to test api.py imports."""
import sys
import traceback

print("[TEST] Starting import test...", flush=True)

try:
    print("[TEST] Importing api module...", flush=True)
    import api
    print("[SUCCESS] API imported successfully!", flush=True)
    print(f"[SUCCESS] App object: {api.app}", flush=True)
except Exception as e:
    print(f"[ERROR] Import failed: {type(e).__name__}", flush=True)
    print(f"[ERROR] Message: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
