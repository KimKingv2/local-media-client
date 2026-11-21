# Flutter source bundle

The base Flutter project is stored as eight base64 text fragments in `parts/`. Tracked patch files under `patches/` add the WebDAV source, catalogue, native MediaKit playback integration, and later playback/scanner/UI and directory-timeout corrections.

From the repository root, reconstruct the exact buildable source with:

```bash
python3 source/reconstruct_source.py --output local-media-client
```

The helper validates the base archive and every compressed/split patch with SHA-256 checksums, extracts the Flutter project, and applies patches in the same order as the GitHub Actions workflow. The output directory must be empty or not yet exist.

The Android and macOS GitHub Actions jobs call this helper directly. Avoid extracting only `parts/` and treating the result as the current app source: the later tracked patches are required.
