# Flutter source bundle

The base Flutter project is stored as eight base64 text fragments in `parts/`. Tracked patch files under `patches/` add the WebDAV source, catalogue, native MediaKit playback integration, and later playback/scanner/UI, directory-timeout, media-library/search/player-control improvements, TMDB metadata scraping, scan/sidecar/artwork-cache reliability fixes, interrupted-scan recovery, local SQLite backup/restore, TinyMediaManager NFO metadata precedence, persistent WebDAV poster/backdrop caching, and selectable portable cache backups.

From the repository root, reconstruct the exact buildable source with:

```bash
python3 source/reconstruct_source.py --output local-media-client
```

The helper validates the base archive and every compressed/split patch with SHA-256 checksums, extracts the Flutter project, and applies patches in the same order as the GitHub Actions workflow. Patch 0031 extends Kodi/TinyMediaManager NFO parsing and ensures local NFO values override TMDB fallback values. Patch 0032 caches recognized WebDAV poster/backdrop images in the app's durable artwork directory, with bounded reads, image-signature checks, and no media-body downloads. Patch 0033 adds `.lmcbackup` portable backups with separate export/import controls for provider scrape cache and cached artwork; credentials and API tokens are always excluded, while legacy raw SQLite imports remain supported. The output directory must be empty or not yet exist.

The Android and macOS GitHub Actions jobs call this helper directly. Avoid extracting only `parts/` and treating the result as the current app source: the later tracked patches are required.
