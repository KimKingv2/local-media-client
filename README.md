# Local Media Client

A local-first media library client for Android TV, Android tablets, Android phones, and macOS. Media stays on the WebDAV server; the app maintains a local catalogue and streams selected files directly.

## Current implementation status

**This is an engineering preview, not a production-ready media centre.**

Implemented:
- WebDAV source setup, connection testing, directory browsing, anonymous access, and HTTP Basic authentication. Saved credentials are kept in OS secure storage.
- Recursive metadata-only scanning for video, subtitle, artwork, and NFO/JSON sidecar files. Scanning does not download video bodies.
- Conservative filename parsing and provisional local grouping for movies, series, seasons, and episodes. This is not provider-based metadata matching.
- Integrated MediaKit/libmpv video player and playback UI for Android and macOS. Playback resolves the WebDAV resource immediately before opening and streams from its HTTP(S) URL rather than copying the movie to local storage.
- A one-byte HTTP Range GET probe for playback access and redirect resolution. The probe cancels the response body; it does not download the video. The client does not require HEAD to succeed.
- Local playback-position persistence and resume, plus play/pause, seeking, and volume controls.
- Selection of embedded audio and subtitle tracks. Same-name external SRT/ASS/SSA/VTT subtitles can be discovered from the parent WebDAV directory and loaded into memory (currently capped at 4 MiB per subtitle file).

The playback engine and UI are integrated, and protocol/unit tests cover the WebDAV request flow. **The CI build does not connect to your live WebDAV server or prove end-to-end playback on every device/server combination.** Your OpenList/WebDAV server and actual media files still need device-level verification.

Not implemented or not production-ready:
- Online metadata scraping or provider matching (TMDB/TVDB etc.), cast/crew details, and an automated poster/backdrop catalogue. NFO/JSON files are indexed but not yet parsed into provider metadata.
- Server-side transcoding or compatibility conversion. The app requests the original remote media; playback depends on the source file, server HTTP behavior, and the bundled media engine.
- Production-grade HDR, multichannel passthrough, codec tuning, and complete Android TV remote-control polish.
- A mature backup/sync system for the local catalogue and playback state across devices.

## Reconstruct the complete Flutter source

The base Flutter archive and subsequent source patches are tracked separately. Use the helper below to verify the checksums, reconstruct the archive, and apply **all** patches in the same order used by GitHub Actions:

\`\`\`bash
python3 source/reconstruct_source.py --output local-media-client
cd local-media-client
flutter pub get
\`\`\`

The script requires Python 3, \`gzip\`, \`tar\`, and the system \`patch\` utility. The output directory must be empty or not yet exist.

Build locally:

\`\`\`bash
./tool/build_android_preview.sh
./tool/build_macos_preview.sh
\`\`\`

For a trusted LAN WebDAV server that uses plain HTTP, explicitly opt in when building locally:

\`\`\`bash
ALLOW_CLEARTEXT_WEB_DAV=1 ./tool/build_android_preview.sh
\`\`\`

## GitHub Actions previews

The workflow reconstructs the exact same source with checksum verification, runs platform-configuration tests, Flutter static analysis and Flutter tests, then builds Android and macOS previews. Successful APK/ZIP artifacts are attached to the workflow run.

For pushes to \`main\`, the preview builds permit plain HTTP so they can connect to common home-LAN WebDAV endpoints. A manually dispatched workflow remains HTTPS-only by default; its \`allow_cleartext_webdav\` option can opt in.

## Security note

**Plain HTTP is not encrypted.** HTTP Basic credentials, media requests, and media data can be observed by anyone able to monitor that network traffic. The main-branch preview packages allow cleartext HTTP for home-LAN testing, so use them only on a trusted network. Use HTTPS for access over the internet, public Wi-Fi, or any untrusted network. The manually dispatched workflow keeps this permission disabled unless explicitly enabled.

The preview does not include a hosted backend, account service, Cloudflare Worker, or mandatory sign-in. Each installation keeps its own local SQLite catalogue and playback state.
