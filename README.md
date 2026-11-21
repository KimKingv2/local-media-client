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
- GitHub Actions workflow template.

Not implemented yet:
- **Metadata scraping**: no TMDB/TVDB/other metadata-provider integration, automatic title matching, poster/backdrop downloading, cast/crew lookup, or manual-match UI.
- Deterministic filename parsing and movie/series/season/episode grouping.
- Actual video playback, subtitle/audio track selection, HDR or multichannel playback.
- Production-ready Android TV and macOS UX.

The current scanner only indexes remote file paths and properties. It does not fetch metadata from an online catalogue and does not download video files. NFO/JSON sidecars are indexed for future parsing, but they are not yet converted into a matched local media catalogue.

## Source code

The complete Flutter source package is stored at `source/local-media-client-source.tar.gz`. Extract it to work with the Flutter project:

```bash
mkdir local-media-client
tar -xzf source/local-media-client-source.tar.gz -C local-media-client
cd local-media-client
```

The archive includes the project README, architecture documents, Dart source, tests, and build scripts.

## Build automation

The GitHub Actions workflow in `.github/workflows/build-previews.yml` unpacks the source bundle, sets up Flutter, runs formatting, static analysis and tests, then builds:
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
