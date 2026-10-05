"""Read-only publication manifest verification; standard library only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(__file__).resolve().parent
manifest = json.loads((DOC / "bundle_manifest.json").read_text())
assert manifest["manifest_self_excluded"] is True
assert not any(Path(row["path"]).name == "bundle_manifest.json" for row in manifest["files"])
for row in manifest["files"]:
    path = ROOT / row["path"]
    assert ".runtime" not in path.parts
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], row["path"]
print(f"bundle files: {len(manifest['files'])} PASS; molecular actions/numeric imports 0")
