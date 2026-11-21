# Local Media Client

A local-first media library client targeting Android TV, Android tablets, Android phones, and macOS.

## Current implementation status

**This is an early engineering preview, not yet a complete media-center app.**

Implemented in the source bundle:
- Local SQLite schema and migrations.
- Standard WebDAV source configuration and directory browsing.
- Anonymous and HTTP Basic authentication, with credentials stored in OS secure storage.
- Recursive metadata-only WebDAV scanner for video, subtitle, artwork, and NFO/JSON sidecar files.
- Android and macOS preview build scripts.
- GitHub Actions workflow for Android and macOS preview builds.

Not implemented yet:
- **Metadata scraping**: no TMDB/TVDB/other metadata-provider integration, automatic title matching, poster/backdrop downloading, cast/crew lookup, or manual-match UI.
- Deterministic filename parsing and movie/series/season/episode grouping.
- Actual video playback, subtitle/audio track selection, HDR or multichannel playback.
- Production-ready Android TV and macOS UX.

The current scanner only indexes remote file paths and properties. It does not fetch metadata from an online catalogue and does not download video files. NFO/JSON sidecars are indexed for future parsing, but they are not yet converted into a matched local media catalogue.

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
