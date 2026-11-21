# Flutter source bundle

The Flutter project is stored as eight base64 text fragments in `parts/` so that GitHub can reliably host and version the source archive.

Reconstruct it from the repository root:

```bash
python3 - <<'PY'
from pathlib import Path
import base64
import hashlib

encoded = "".join(
    part.read_text(encoding="ascii").strip()
    for part in sorted(Path("source/parts").glob("*.b64"))
)
archive = base64.b64decode(encoded, validate=True)
digest = hashlib.sha256(archive).hexdigest()
expected = "4d15686e484d8ded1b64d850ad8fce1827048c07ce20a997037b201598009bcf"
if digest != expected:
    raise SystemExit(f"Checksum mismatch: {digest}")
Path("/tmp/local-media-client-source.tar.gz").write_bytes(archive)
print(f"Verified {len(archive)} bytes: {digest}")
PY
mkdir -p local-media-client
tar -xzf /tmp/local-media-client-source.tar.gz -C local-media-client
```

The Android and macOS GitHub Actions jobs perform the same reconstruction and checksum verification before building.
