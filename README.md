# Local Media Client

A local-first media library client for Android TV, Android tablets, Android phones, and macOS. Media stays on the WebDAV server; the app maintains a local catalogue and streams selected files directly.

## Current implementation status

**This is an engineering preview, not a production-ready media centre.**

Implemented:
- WebDAV source setup, connection testing, directory browsing, anonymous access, and HTTP Basic authentication. Saved credentials are kept in OS secure storage.
- Recursive WebDAV scanning for video, subtitle, artwork, and NFO/JSON sidecar files. Video bodies are never fetched during scanning. Index and grouping changes are committed only after a complete traversal; failed/cancelled scans keep the previous completed index. Small NFO/JSON sidecars are fetched separately (up to 1 MiB each). TinyMediaManager Kodi-compatible NFO is the primary metadata source and parses titles, original/sort titles, release dates, runtime, ratings, genres, countries, studios, directors, writers, actors, and TMDB/IMDb identifiers. It recognises local artwork references and common folder files such as `poster.jpg`, `folder.jpg`, `cover.jpg`, `thumb.jpg`, `fanart.jpg`, and `backdrop.jpg`; selected images are downloaded separately with a 20 MiB per-file limit into durable app artwork storage. Cover-only folders are supported. TMDB remains a fallback and never overwrites available NFO fields or WebDAV folder artwork. Artwork pruning uses a 1 GiB soft budget and deletes only unreferenced images.
- Filename parsing and local grouping for movies, series, seasons, and episodes, including explicit anime folder conventions. A work is displayed once even when multiple encodes/files exist; searching covers localized/original titles, sort titles, file names, and nested episode files.
- Integrated MediaKit/libmpv video player and playback UI for Android and macOS. Playback resolves the WebDAV resource immediately before opening and streams from its HTTP(S) URL rather than copying the movie to local storage.
- A one-byte HTTP Range GET probe for playback access and redirect resolution. The probe cancels the response body; it does not download the video. The client does not require HEAD to succeed.
- Directory listing (WebDAV PROPFIND Depth: 1) has a separate 45-second timeout for slower remote-mounted storage; playback probes and single-resource requests retain the shorter 20-second timeout.
- Database-backed movie, series, and continue-watching pages, with episode drill-down for grouped series and title/file-name search. Series and episodic-anime detail pages show season cards; episode counts include only episodes with an indexed video file. Anime navigation exists, but automatic anime classification is not yet implemented.
- Local playback-position persistence and resume, including forced saves when the app moves into the background; play/pause, seeking, and a user-facing volume/mute control.
- Selection of embedded audio and subtitle tracks. Same-name external SRT/ASS/SSA/VTT subtitles can be discovered from the parent WebDAV directory and loaded into memory (currently capped at 4 MiB per subtitle file).
- TMDB metadata search and manual matching for scanned movies, series, and explicitly classified anime.
- Portable `.lmcbackup` ZIP export/import in Settings. Export and import each have an independent choice to include cached scrape extensions, TMDB detail responses, and downloaded poster/backdrop/person images. When included, artwork is bundled and both database columns and nested metadata paths are rewritten to portable bundle paths; restore writes files to the new device's app artwork directory and repairs those paths. When excluded, normalized catalogue titles/metadata, sources, file indexes and playback positions remain, while NFO/TMDB cache payloads and downloaded images are omitted. Bundles are capped at 512 MiB (128 MiB database, 384 MiB artwork, 20 MiB per image, and 2,000 images), and ZIP size claims are checked before decompression. Incoming database integrity/schema is validated and a rollback copy is kept if restore fails. Legacy raw SQLite backups remain importable. WebDAV passwords and TMDB tokens are never included; backup files contain server URLs and library data, so store them securely. Configure a TMDB API Read Access Token in Settings → Metadata; the token is stored in OS secure storage and is sent only over HTTPS. Confirmed metadata and detail responses are saved locally; detail responses are read-through cached for 30 days. Poster/backdrop images are stored in persistent Application Support artwork storage, shared by image identity, and reused offline. Image cache pruning has a 1 GiB soft budget and removes only unreferenced files; referenced images are never deleted automatically. Failed image downloads are reported while previous images are preserved.

The playback engine and UI are integrated, and protocol/unit tests cover the WebDAV request flow. **The CI build does not connect to your live WebDAV server or prove end-to-end playback on every device/server combination.** Your OpenList/WebDAV server and actual media files still need device-level verification.

The Android APK and macOS app produced by this workflow are Flutter **debug builds**, intended for evaluation rather than production or store distribution. The Android APK is marked debuggable. The macOS workflow does not perform Developer ID signing or notarization.

Android preview signing is stable only when the repository Actions secret `ANDROID_DEBUG_KEYSTORE_BASE64` is configured. Without it, each hosted runner may generate a different debug certificate, and the APK may not update an existing installation. See **Keep Android preview signing stable** below.

Not implemented or not production-ready:
- Automatic unattended/batch TMDB matching, TVDB provider support, confidence-ranked auto matching, season/episode-specific TMDB metadata, advanced content-aware anime classification, and full NFO/JSON standard coverage. Anime classification currently relies on explicit folder naming conventions. Sidecar parsing targets common Kodi/TinyMediaManager NFO fields and simple JSON, not every NFO dialect. Cached backdrop images are available locally but are not yet presented as a full-screen detail backdrop.
- Server-side transcoding or compatibility conversion. The app requests the original remote media; playback depends on the source file, server HTTP behavior, and the bundled media engine.
- Production-grade HDR, multichannel passthrough, codec tuning, and complete Android TV remote-control polish.
- Scheduled automatic backups, cross-device catalogue sync, and a managed off-device backup service.

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Reconstruct the complete Flutter source

The base Flutter archive and subsequent source patches are tracked separately. Use the helper below to verify the checksums, reconstruct the archive, and apply **all** patches in the same order used by GitHub Actions:

```bash
python3 source/reconstruct_source.py --output local-media-client
cd local-media-client
flutter pub get
```

The script requires Python 3, `gzip`, `tar`, and the system `patch` utility. The output directory must be empty or not yet exist.

Build locally:

```bash
./tool/build_android_preview.sh
./tool/build_macos_preview.sh
```

For a trusted LAN WebDAV server that uses plain HTTP, explicitly opt in when building locally:

```bash
ALLOW_CLEARTEXT_WEB_DAV=1 ./tool/build_android_preview.sh
```

## GitHub Actions previews

The workflow reconstructs the exact same source with checksum verification, runs platform-configuration tests, Flutter static analysis and Flutter tests, then builds Android and macOS previews. Successful APK/ZIP artifacts are attached to the workflow run.

Push and pull-request builds default to HTTPS-only. To generate a preview for a plain-HTTP home-LAN WebDAV server, open GitHub Actions → **Build installable previews** → **Run workflow**, then explicitly enable `allow_cleartext_webdav`.

## Keep Android preview signing stable

To let future Android preview APKs update the same installed app, create a private debug keystore once on a trusted computer and store it as a GitHub Actions repository secret. Run this on macOS from the directory where you want to keep the keystore:

```bash
keytool -genkeypair -v \
  -keystore local-media-debug.keystore \
  -storepass android \
  -alias androiddebugkey \
  -keypass android \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Local Media Client"
base64 -i local-media-debug.keystore | tr -d '\n'
```

Copy the base64 output into GitHub → **Settings → Secrets and variables → Actions → New repository secret**, named `ANDROID_DEBUG_KEYSTORE_BASE64`. Do not commit the keystore or its base64 contents to the repository. Keep a separate secure copy of the keystore: losing it means future builds cannot keep the same signing identity.

After the secret is configured, subsequent Android preview builds reuse that signing certificate. This cannot recover the private debug keys from earlier hosted runs, so APKs from earlier runs may still require a database export and a fresh installation. The app's local SQLite backup/restore can help preserve the catalogue, but WebDAV passwords and TMDB tokens stored in secure storage must be entered again after reinstalling.

## Security note

**Plain HTTP is not encrypted.** When `allow_cleartext_webdav` is enabled, Android sets `usesCleartextTraffic=true` and macOS sets `NSAllowsArbitraryLoads=true` for the whole app. This is not restricted to `192.168.31.185`, a hostname, or a private IP range. HTTP Basic credentials, media requests, and media data can be observed by anyone able to monitor that network traffic. Enable this only for a trusted LAN; use HTTPS over the internet, public Wi-Fi, or any untrusted network.

The preview does not include a hosted backend, account service, Cloudflare Worker, or mandatory sign-in. Each installation keeps its own local SQLite catalogue and playback state.
