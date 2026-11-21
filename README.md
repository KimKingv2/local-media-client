# Local Media Client

A local-first media library client targeting Android TV, Android tablets, Android phones, and macOS.

## Current implementation status

**This is an early engineering preview, not yet a complete media-center app.**

Implemented in the source bundle:
- Local SQLite schema and migrations.
- Standard WebDAV source configuration and directory browsing.
- Anonymous and HTTP Basic authentication, with credentials stored in OS secure storage.
- Recursive metadata-only WebDAV scanner for video, subtitle, artwork, and NFO/JSON sidecar files.
- Conservative filename parsing for common movie-year, SxxExx, 1x02, Chinese season/episode, and Season-folder numbering patterns.
- Local provisional catalogue grouping into movie and series → season → episode records, linked to the remote WebDAV file rows.
- Android and macOS preview build scripts.
- GitHub Actions workflow for Android and macOS preview builds.

Not implemented yet:
- **Metadata scraping**: no TMDB/TVDB/other metadata-provider integration, provider-based title matching, poster/backdrop downloading, cast/crew lookup, or manual-match UI. The current filename parser only creates provisional local titles and hierarchy; it does not confirm identity against an online catalogue.
- Actual video playback, subtitle/audio track selection, HDR or multichannel playback.
- Production-ready Android TV and macOS UX.

The scanner indexes remote paths and properties, then uses filenames and season folders to build a provisional local catalogue. Unrecognized files remain unmatched instead of being forced into a category. It does not fetch metadata from an online catalogue and does not download video files. NFO/JSON sidecars are indexed for future parsing, but are not yet converted into provider-matched metadata.

## Source code

The compressed Flutter source is stored as text-safe base64 parts in `source/parts/`. Reconstruct, extract, and apply the tracked source fixes with:

```bash
python3 - <<'PY'
from pathlib import Path
import base64

encoded = "".join(
    part.read_text(encoding="ascii").strip()
    for part in sorted(Path("source/parts").glob("*.b64"))
)
Path("/tmp/local-media-client-source.tar.gz").write_bytes(
    base64.b64decode(encoded, validate=True)
)
PY
mkdir -p local-media-client
tar -xzf /tmp/local-media-client-source.tar.gz -C local-media-client
for fix in source/patches/*.patch; do
  patch -d local-media-client -p1 < "$fix"
done
python3 - <<'PY'
from pathlib import Path
import base64, gzip, hashlib
encoded = Path("source/patches/0005-parse-and-group-local-media.patch.gz.b64").read_text().strip()
compressed = base64.b64decode(encoded, validate=True)
expected = "ff7921fc5a8c6f70ed4bffc6640ddc76d9b3bea02815ab553ad5d973054e74e6"
if hashlib.sha256(compressed).hexdigest() != expected:
    raise SystemExit("Media catalogue patch checksum mismatch")
Path("/tmp/media-catalogue.patch").write_bytes(gzip.decompress(compressed))
PY
patch -d local-media-client -p1 < /tmp/media-catalogue.patch
cd local-media-client
```

The Actions workflow performs the same reconstruction and applies each tracked patch before compiling. This keeps small source corrections reviewable without repeatedly re-uploading the compressed archive.

## Build automation

The GitHub Actions workflow in `.github/workflows/build-previews.yml` reconstructs and checksum-verifies the source archive, applies tracked source patches, sets up Flutter, runs formatting, static analysis and tests, then builds:
- Android preview APK for Android TV / tablet / phone.
- macOS app preview ZIP.

Successful builds are uploaded as workflow artifacts for 30 days.

## Product architecture

- No hosted backend, Cloudflare, D1, Workers, or mandatory account.
- Metadata and artwork will be stored locally on each installation.
- Media files remain on the WebDAV server and are not copied into the app.
- Standard WebDAV is the only remote media protocol in the initial scope.
- Each device has its own local SQLite catalogue and artwork cache.

## Security note

HTTPS WebDAV is strongly recommended. HTTP Basic credentials and media traffic are unencrypted over plain HTTP. The workflow keeps cleartext WebDAV disabled by default.
