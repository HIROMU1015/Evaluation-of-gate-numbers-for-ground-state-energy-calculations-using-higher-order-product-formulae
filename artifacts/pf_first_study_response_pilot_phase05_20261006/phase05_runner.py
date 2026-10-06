"""Reviewable production boundary, intentionally disabled in Phase 0.5."""
import argparse
import hashlib
from pathlib import Path

def verify_source_hash(path,expected):
    # Bytes only: no production matrix/vector decoding or scientific action.
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=expected:
        raise ValueError("source SHA-256 mismatch; stop before decode")
    return actual

def main(argv=None):
    parser=argparse.ArgumentParser()
    phase=parser.add_mutually_exclusive_group(required=True)
    phase.add_argument("--phase-a",action="store_true")
    phase.add_argument("--phase-b",action="store_true")
    parser.parse_args(argv)
    raise RuntimeError("Phase 0.5 is design-only. H4 production runner is disabled; a separately authorized adapter is required.")

if __name__=="__main__":
    main()
