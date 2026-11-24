#!/usr/bin/env python3
"""Reconstruct the Flutter source archive and apply every tracked patch."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PARTS = [f"{index:02d}.b64" for index in range(8)]
ARCHIVE_LENGTH = 82160
ARCHIVE_SHA256 = "4d15686e484d8ded1b64d850ad8fce1827048c07ce20a997037b201598009bcf"
PATCH_0005_SHA256 = "ff7921fc5a8c6f70ed4bffc6640ddc76d9b3bea02815ab553ad5d973054e74e6"
PATCH_0006_PART_SHA256 = {
    "00.b64": "f3b122c81ceaf663c481dc447bde5514ac3ab0c23d4a99280fef92044cafdc18",
    "01.b64": "8b777241e8068a065f58779975f2722f355222b2010c99e9b46e1a80e26bd7e3",
    "02.b64": "f8e8434e3f389b8f43657ebc6ade6254a260b1e3fd7bec116b3b63108cda2419",
    "03.b64": "0cae7238a95f4815294330c07e03f7a345116c35cc264277bbf740508401d55f",
    "04.b64": "07768e7738150e02087d7f10a1f54e5b9c5dceb25b2d9081eeda5950d1a65f1e",
    "05.b64": "51dced49cb8ab3ce9e61f0167b2d77d7121140593fe88fd2415d4c2317c6cbc1",
    "06.b64": "620793607775e33daf59666f4f8ae836fb788d9f4ea4da9c12eb524e2838327e",
    "07.b64": "fbbc070ac33af1b4c69ac13251664946023ce5b9da2e9e40da10366c000c04c9",
}
PATCH_0006_SHA256 = "2ded2454c07b03baebdefef64dc481b4190bdc283f487760b92d9845e26d1b71"
PATCH_0007_SHA256 = "7c70e4851e1af722866287498530286a880779081cb2f78c9c3e0591f922a3bb"
PATCH_0008_SHA256 = "289ff2da09b28627bbc4b8f65870ef2b8cec01438d69dce99cd374fdfc36cf45"
PATCH_0009_SHA256 = "d631d9d432da3df51a261e8cb1b96c7a31a41728ee8110ac65afb4de1320842c"
PATCH_0010_SHA256 = "df26a6a718461ad4397b68b203d15bfc82a89373da2c2a4c4ab4a7d8ecb3d14a"
PATCH_0011_PART_SHA256 = {
    "00": "6945299547b6459658f014b47e4a6e9ad2c7d4c44c5fa480161b25eec3463f22",
    "01": "0bade1d26e8275ed57b15a9e43834114a13d0a8f13f067f90686190f11f8c6b7",
    "02": "556af48347572339e0e6865d1379df4514561948f1475d47eecb0011eb66d96c",
    "03": "0dad3e374747c25949e61c858e0b1cd37437dbdbb531867c1f009dd85d3c92f6",
}
PATCH_0012_SHA256 = "2ac5c4a1d53f83fb901360fe2cc9d65a7e852db7ed125fbdc1851d969c741011"
PATCH_0013_SHA256 = "3923ae8af56820e11abf1e8bc351891197e8bfd05073b01358f634810c8576a3"
PATCH_0014_SHA256 = "9d23c3f49ba34ccc88e892ebe54bde4fd4c05342d14a1497d78f5f5649395e7d"
PATCH_0015_SHA256 = "c4a446aa1fab4eb5c1f883a207edeca38465ce14c86809b0f7c9d6228c82711b"
PATCH_0016_SHA256 = "5f1cf59d1271d0e4b118d351025fd82f90028499d503d813a770dd7e9b7cc1bf"
PATCH_0017_SHA256 = "c02c6638dd9bc9151cc8ef546a7d0e4c351d7c9e3f190b7cb697857f541f26e2"
PATCH_0018_SHA256 = "769700767b9cd505e2458bb46dd5572f296a08d050218c946e9b460ff9971757"
PATCH_0019_SHA256 = "cfa462df5a93c6f045a87d1ee6b669a4733fbd5324a10c3c0c0a9b9374276f87"
PATCH_0020_SHA256 = "e17a551c4b860bcc07185e51be11da5921d0c30571ece4c35c1f902a5534e209"
PATCH_0021_SHA256 = "943fbc177902f5d659229a9d83d6681a657446cc7296896ac46bdb4a1325f427"
PATCH_0022_SHA256 = "794dd243dbd232545a88d0f8878ce79bcc93ca115427d005aa0959d019077bd4"
PATCH_0023_SHA256 = "bdd5ef6a493ab97759f76ee1c1cd80067391f60ad9e7934f1620748db93bd528"
PATCH_0024_SHA256 = "60833cb0b43b568f2c99e4cadaa497831b8b794145a3540bc8bcd7df912dfa5e"
PATCH_0025_SHA256 = "dc19106a89b6198762d8c1958ab84976238d4a0cb860023df66dc4c2f4cd560a"
PATCH_0026_SHA256 = "339d52b208297366057d3e834a50b13175e8d7afaa8db812545f5e5201bda5d2"
PATCH_0027_SHA256 = "358483ad63e238cd6212eb8fd380ff5938b43f5f269c5b01f3df217798bfc907"
PATCH_0028_SHA256 = "f5df05cd3e6d0db7824cbb1d3874430e735476e488495365479249214634c31b"
PATCH_0029_SHA256 = "530c3a044eeb27e0dea25ec801ba56f7dcb62fd3bd7f5a4f563b8464832e37eb"
PATCH_0030_SHA256 = "d5c76ca9de459eb923e3f482233f1f572d1a0cf943c49ee0e4fdcc39415d8b2c"
PATCH_0031_PART_SHA256 = {
    "00.b64": "b8e3b42ae32c7d23989bf6aac1503055e41a21cb8b957ee4688339ae91d54a5b",
    "01.b64": "5f051f785821bd5ee5b1dfaa333956539f4d6d40577d45329ddb413bfd3c5dee",
    "02.b64": "3424116f90e0b017cd711e8ab318248bfcedc8e94a2c2282a42d1d8f9e9eb44d",
}
PATCH_0031_SHA256 = "c037086044aea39d2f5ccce09fcab78b1a348c16998acfb916308d2a828f03d7"
PATCH_0032_PART_SHA256 = {
    "00.b64": "8bd26711bf4f9dba2ecea8d47ca1258be0cfca468b0e343a83bc351a140542f8",
    "01.b64": "624c525c445b4d6c87c3866572950a7c5ae1771013faff37aca1a6ade1d02f7a",
    "02.b64": "57e2074387e39b707ed4d923cf47e716e6d4a355e7209f42165ec9c73f782426",
    "03.b64": "f95862ca46c746c4a7095caea50ca5b4763d538e59f375088a436fd30874847b",
}
PATCH_0032_SHA256 = "9e48dc14e83505da8fe8c0879c37d2d1e1b6ab36fcd4114f1917bfd0ef9f585c"
PATCH_0033_PART_SHA256 = {
    "00.b64": "2614671d3febae58fc47dc5eb6759e1b062a7eb3faf13cffd27febaf871adb30",
    "01.b64": "0f96ba579f6f3b7cf20adde67346f9f3eec665524ceab12d59a7fa3d385278af",
    "02.b64": "fc4086e54aae52ff19a98e7bcb3e3a3374c9c15530422eecddf4e1521c35c8f4",
    "03.b64": "634a00f028263d7092a16fdb66476795082d98ca9f5ee7d5d6203b3409272c9e",
    "04.b64": "077a7a16267b62f84f2fb2cdd131619cb1c4653103f5324c9de07dfbf0b05efb",
    "05.b64": "f4a6ef1cf27669f7ee4a8412583ce6a0612dfb53704f6dcb7b6e9f9bc87d02bf",
    "06.b64": "f407b0f18db584ea1113c94277a7003579dcfd552edf2037ffe5568f53993cbe",
    "07.b64": "6a97fb7ea25b48840241bdd5707c64c45578726651d157d8c17b17121c2d04ae",
    "08.b64": "00934257dd7de1961d149d9c0b45dfb99bf7995f18941087941615a797ea0d2f",
    "09.b64": "55b9453be4cafb290f20307b5d74c332a34a104b9c10c476c17971b1ab9ab337",
    "10.b64": "49400ccfc664a3ad5bc1967fb3df23505ec72b9c049dab400a78b7f5e0e0b17d",
    "11.b64": "fc6c1a28d07ccb48f6d6747ff4fcb7f4b7c170398831e8e4e124b8fb8dd8e0ab",
}
PATCH_0033_SHA256 = "db85fa8c12f3f92de8410d211b97b8d93ba634fa763dd266d5cfca032d7db7ed"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_base64(path: Path) -> bytes:
    try:
        return base64.b64decode(path.read_text(encoding="ascii").strip(), validate=True)
    except (OSError, UnicodeError, ValueError) as exc:
        raise SystemExit(f"Invalid base64 payload {path.relative_to(ROOT)}: {exc}") from exc


def apply_patch(output: Path, patch_data: bytes, label: str) -> None:
    result = subprocess.run(
        ["patch", "-d", str(output), "-p1"],
        input=patch_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        print(result.stdout.decode("utf-8", errors="replace"), end="")
        raise SystemExit(f"Failed to apply {label} (exit {result.returncode}).")
    print(result.stdout.decode("utf-8", errors="replace"), end="")


def verified_gzip_patch(path: Path, expected_sha: str, label: str) -> bytes:
    compressed = decode_base64(path)
    actual = sha256(compressed)
    if actual != expected_sha:
        raise SystemExit(f"{label} checksum mismatch: {actual}")
    try:
        return gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise SystemExit(f"{label} is not a valid gzip payload: {exc}") from exc


def reconstruct(output: Path) -> None:
    parts_dir = ROOT / "source" / "parts"
    archive_parts = sorted(parts_dir.glob("*.b64"))
    if [part.name for part in archive_parts] != ARCHIVE_PARTS:
        raise SystemExit("Source archive parts are incomplete or unexpected.")
    encoded = "".join(part.read_text(encoding="ascii").strip() for part in archive_parts)
    if len(encoded) != ARCHIVE_LENGTH:
        raise SystemExit(f"Unexpected source payload length: {len(encoded)}")
    try:
        archive = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise SystemExit(f"Invalid source archive base64: {exc}") from exc
    actual = sha256(archive)
    if actual != ARCHIVE_SHA256:
        raise SystemExit(f"Source archive checksum mismatch: {actual}")

    output = output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SystemExit(f"Output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="local-media-source-") as temporary:
        archive_path = Path(temporary) / "source.tar.gz"
        archive_path.write_bytes(archive)
        subprocess.run(["gzip", "-t", str(archive_path)], check=True)
        subprocess.run(["tar", "-xzf", str(archive_path), "-C", str(output)], check=True)

    for patch_path in sorted((ROOT / "source" / "patches").glob("*.patch")):
        apply_patch(output, patch_path.read_bytes(), patch_path.name)

    patch_0005 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0005-parse-and-group-local-media.patch.gz.b64",
        PATCH_0005_SHA256,
        "Media catalogue patch",
    )
    apply_patch(output, patch_0005, "0005 media catalogue patch")

    playback_parts_dir = ROOT / "source" / "patches" / "0006-parts"
    playback_parts = sorted(playback_parts_dir.glob("*.b64"))
    if [part.name for part in playback_parts] != sorted(PATCH_0006_PART_SHA256):
        raise SystemExit("Native playback patch parts are incomplete or unexpected.")
    encoded_parts = []
    for part in playback_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != PATCH_0006_PART_SHA256[part.name]:
            raise SystemExit(f"{part.name} checksum mismatch: {actual}")
        encoded_parts.append(raw.decode("ascii").strip())
    try:
        compressed = base64.b64decode("".join(encoded_parts), validate=True)
        actual = sha256(compressed)
        if actual != PATCH_0006_SHA256:
            raise SystemExit(f"Native playback patch checksum mismatch: {actual}")
        patch_0006 = gzip.decompress(compressed)
    except (ValueError, OSError, EOFError) as exc:
        raise SystemExit(f"Invalid native playback patch payload: {exc}") from exc
    apply_patch(output, patch_0006, "0006 native playback patch")

    patch_0007 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0007-fix-webdav-playback-scan-ui.patch.gz.b64",
        PATCH_0007_SHA256,
        "Post-playback patch",
    )
    apply_patch(output, patch_0007, "0007 WebDAV playback, scanner and UI patch")

    patch_0008 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0008-extend-webdav-directory-timeout.patch.gz.b64",
        PATCH_0008_SHA256,
        "Directory listing timeout patch",
    )
    apply_patch(output, patch_0008, "0008 extended WebDAV directory listing timeout")

    patch_0009 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0009-library-search-volume-resume.patch.gz.b64",
        PATCH_0009_SHA256,
        "Library, search and playback controls patch",
    )
    apply_patch(output, patch_0009, "0009 library, search and playback controls")

    patch_0010 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0010-tmdb-metadata-scraping.patch.gz.b64",
        PATCH_0010_SHA256,
        "TMDB metadata scraping patch",
    )
    apply_patch(output, patch_0010, "0010 TMDB metadata scraping")

    for part_index, expected_sha in PATCH_0011_PART_SHA256.items():
        suffix = part_index
        patch_0011_part = verified_gzip_patch(
            ROOT / "source" / "patches" / f"0011-self-audit-{suffix}.patch.gz.b64",
            expected_sha,
            f"Self-audit reliability patch part {suffix}",
        )
        apply_patch(
            output,
            patch_0011_part,
            f"0011 self-audit reliability part {suffix}",
        )

    patch_0012 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0012-fix-sidecar-nullable-casts.patch.gz.b64",
        PATCH_0012_SHA256,
        "Nullable cast parser fix",
    )
    apply_patch(output, patch_0012, "0012 nullable cast parser fix")

    patch_0013 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0013-runtime-fixes.patch.gz.b64",
        PATCH_0013_SHA256,
        "Runtime compatibility and diagnostics patch",
    )
    apply_patch(output, patch_0013, "0013 runtime compatibility and diagnostics")

    patch_0014 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0014-fix-proxy-promotion.patch.gz.b64",
        PATCH_0014_SHA256,
        "TMDB proxy nullable promotion fix",
    )
    apply_patch(output, patch_0014, "0014 TMDB proxy nullable promotion fix")

    patch_0015 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0015-scanner-and-tmdb-diagnostics.patch.gz.b64",
        PATCH_0015_SHA256,
        "Scanner sidecar and TMDB network diagnostics patch",
    )
    apply_patch(output, patch_0015, "0015 scanner sidecar and TMDB network diagnostics")

    patch_0016 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0016-sidecar-association-and-proxy-test.patch.gz.b64",
        PATCH_0016_SHA256,
        "Localized sidecar matching and proxy test fix",
    )
    apply_patch(output, patch_0016, "0016 localized sidecar matching and proxy test")

    patch_0017 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0017-direct-tmdb-no-worker.patch.gz.b64",
        PATCH_0017_SHA256,
        "Direct-client TMDB API patch",
    )
    apply_patch(output, patch_0017, "0017 direct-client TMDB API")

    patch_0018 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0018-remove-provider-proxy.patch.gz.b64",
        PATCH_0018_SHA256,
        "Remove optional TMDB proxy support",
    )
    apply_patch(output, patch_0018, "0018 remove optional TMDB proxy support")

    patch_0019 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0019-resolve-sidecar-item-robustly.patch.gz.b64",
        PATCH_0019_SHA256,
        "Resolve scanned sidecars against persisted media items",
    )
    apply_patch(output, patch_0019, "0019 robust sidecar work resolution")

    patch_0020 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0020-remove-unused-sidecar-path.patch.gz.b64",
        PATCH_0020_SHA256,
        "Remove unused sidecar path",
    )
    apply_patch(output, patch_0020, "0020 remove unused sidecar path")

    patch_0021 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0021-sidecar-ci-diagnostics.patch.gz.b64",
        PATCH_0021_SHA256,
        "Sidecar CI diagnostics patch",
    )
    apply_patch(output, patch_0021, "0021 sidecar CI diagnostics")

    patch_0022 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0022-print-caught-sidecar-error.patch.gz.b64",
        PATCH_0022_SHA256,
        "Caught sidecar read error diagnostics patch",
    )
    apply_patch(output, patch_0022, "0022 caught sidecar read error diagnostics")

    patch_0023 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0023-fix-utf8-nfo-test-fixture-and-remove-debug.patch.gz.b64",
        PATCH_0023_SHA256,
        "Fix UTF-8 NFO test fixture and remove diagnostics",
    )
    apply_patch(output, patch_0023, "0023 UTF-8 NFO test fixture")

    patch_0024 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0024-reliable-partial-scan-index.patch.gz.b64",
        PATCH_0024_SHA256,
        "Reliable partial WebDAV scan indexing patch",
    )
    apply_patch(output, patch_0024, "0024 reliable partial scan indexing")

    patch_0025_parts_dir = ROOT / "source" / "patches" / "0025-parts"
    patch_0025_parts = sorted(patch_0025_parts_dir.glob("*.b64"))
    expected_patch_0025_parts = ["00.b64", "01.b64", "02.b64", "03.b64"]
    if [part.name for part in patch_0025_parts] != expected_patch_0025_parts:
        raise SystemExit("Scan resilience patch parts are incomplete or unexpected.")
    encoded_patch_0025 = "".join(
        part.read_text(encoding="ascii").strip() for part in patch_0025_parts
    )
    try:
        compressed_patch_0025 = base64.b64decode(
            encoded_patch_0025, validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid scan resilience patch base64: {exc}") from exc
    actual_patch_0025_sha256 = sha256(compressed_patch_0025)
    if actual_patch_0025_sha256 != PATCH_0025_SHA256:
        raise SystemExit(
            f"Scan resilience patch checksum mismatch: {actual_patch_0025_sha256}"
        )
    try:
        patch_0025 = gzip.decompress(compressed_patch_0025)
    except (OSError, EOFError) as exc:
        raise SystemExit(
            f"Scan resilience patch is not a valid gzip payload: {exc}"
        ) from exc
    apply_patch(output, patch_0025, "0025 scan resilience self-audit")

    patch_0026 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0026-interrupted-scan-recovery.patch.gz.b64",
        PATCH_0026_SHA256,
        "Interrupted scan recovery patch",
    )
    apply_patch(output, patch_0026, "0026 interrupted scan recovery")

    patch_0027 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0027-local-db-backup.patch.gz.b64",
        PATCH_0027_SHA256,
        "Local database backup and restore patch",
    )
    apply_patch(output, patch_0027, "0027 local database backup and restore")

    patch_0028 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0028-season-cards-for-series-anime.patch.gz.b64",
        PATCH_0028_SHA256,
        "Season cards for series and episodic anime",
    )
    apply_patch(output, patch_0028, "0028 season cards for series and episodic anime")

    patch_0029 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0029-playable-episode-counts.patch.gz.b64",
        PATCH_0029_SHA256,
        "Playable episode counts for series and anime library entries",
    )
    apply_patch(output, patch_0029, "0029 playable episode counts")

    patch_0030 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0030-fix-anime-count-query.patch.gz.b64",
        PATCH_0030_SHA256,
        "Fix anime playable episode count query",
    )
    apply_patch(output, patch_0030, "0030 fix anime playable episode count query")

    patch_0031_parts_dir = ROOT / "source" / "patches" / "0031-parts"
    patch_0031_parts = sorted(patch_0031_parts_dir.glob("*.b64"))
    if [part.name for part in patch_0031_parts] != sorted(PATCH_0031_PART_SHA256):
        raise SystemExit("TinyMediaManager metadata patch parts are incomplete or unexpected.")
    encoded_patch_0031 = []
    for part in patch_0031_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != PATCH_0031_PART_SHA256[part.name]:
            raise SystemExit(f"{part.name} checksum mismatch: {actual}")
        encoded_patch_0031.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0031 = base64.b64decode(
            "".join(encoded_patch_0031), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid TinyMediaManager metadata patch base64: {exc}") from exc
    actual_patch_0031_sha256 = sha256(compressed_patch_0031)
    if actual_patch_0031_sha256 != PATCH_0031_SHA256:
        raise SystemExit(
            f"TinyMediaManager metadata patch checksum mismatch: {actual_patch_0031_sha256}"
        )
    try:
        patch_0031 = gzip.decompress(compressed_patch_0031)
    except (OSError, EOFError) as exc:
        raise SystemExit(
            f"TinyMediaManager metadata patch is not a valid gzip payload: {exc}"
        ) from exc
    apply_patch(output, patch_0031, "0031 TinyMediaManager NFO metadata priority")

    patch_0032_parts_dir = ROOT / "source" / "patches" / "0032-parts"
    patch_0032_parts = sorted(patch_0032_parts_dir.glob("*.b64"))
    if [part.name for part in patch_0032_parts] != sorted(PATCH_0032_PART_SHA256):
        raise SystemExit("WebDAV artwork cache patch parts are incomplete or unexpected.")
    encoded_patch_0032 = []
    for part in patch_0032_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != PATCH_0032_PART_SHA256[part.name]:
            raise SystemExit(f"{part.name} checksum mismatch: {actual}")
        encoded_patch_0032.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0032 = base64.b64decode(
            "".join(encoded_patch_0032), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid WebDAV artwork cache patch base64: {exc}") from exc
    actual_patch_0032_sha256 = sha256(compressed_patch_0032)
    if actual_patch_0032_sha256 != PATCH_0032_SHA256:
        raise SystemExit(
            f"WebDAV artwork cache patch checksum mismatch: {actual_patch_0032_sha256}"
        )
    try:
        patch_0032 = gzip.decompress(compressed_patch_0032)
    except (OSError, EOFError) as exc:
        raise SystemExit(
            f"WebDAV artwork cache patch is not a valid gzip payload: {exc}"
        ) from exc
    apply_patch(output, patch_0032, "0032 persistent WebDAV artwork cache")

    patch_0033_parts_dir = ROOT / "source" / "patches" / "0033-parts"
    patch_0033_parts = sorted(patch_0033_parts_dir.glob("*.b64"))
    if [part.name for part in patch_0033_parts] != sorted(PATCH_0033_PART_SHA256):
        raise SystemExit("Portable scrape-cache backup patch parts are incomplete or unexpected.")
    encoded_patch_0033 = []
    for part in patch_0033_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != PATCH_0033_PART_SHA256[part.name]:
            raise SystemExit(f"{part.name} checksum mismatch: {actual}")
        encoded_patch_0033.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0033 = base64.b64decode(
            "".join(encoded_patch_0033), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid portable scrape-cache backup patch base64: {exc}") from exc
    actual_patch_0033_sha256 = sha256(compressed_patch_0033)
    if actual_patch_0033_sha256 != PATCH_0033_SHA256:
        raise SystemExit(
            f"Portable scrape-cache backup patch checksum mismatch: {actual_patch_0033_sha256}"
        )
    try:
        patch_0033 = gzip.decompress(compressed_patch_0033)
    except (OSError, EOFError) as exc:
        raise SystemExit(
            f"Portable scrape-cache backup patch is not a valid gzip payload: {exc}"
        ) from exc
    apply_patch(output, patch_0033, "0033 portable scrape-cache backup")

    # Some patch-tool versions may already find the corrected close call in
    # patch 0033's resulting source. Verify patch 0034 either way, then apply
    # only when the old nullable temporary variable is still present.
    patch_0034 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0034-fix-backup-null-promotion.patch.gz.b64",
        "a8274c27db57e587b6b131b15f40599ea68ad9c3a8184e0d497bbe326637797d",
        "Portable backup null-promotion analyzer fix",
    )
    backup_service = output / "lib" / "core" / "database" / "local_database_backup_service.dart"
    backup_source = backup_service.read_text(encoding="utf-8")
    old_nullable_close = (
        "      final openedDatabase = database;\n"
        "      if (openedDatabase != null) await openedDatabase.close();"
    )
    if old_nullable_close in backup_source:
        backup_service.write_text(
            backup_source.replace(
                old_nullable_close,
                "      await database.close();",
                1,
            ),
            encoding="utf-8",
        )
        print("0034 portable backup null-promotion analyzer fix applied.")
    elif "      await database.close();" in backup_source:
        print("0034 portable backup null-promotion analyzer fix already present; skipped.")
    else:
        raise SystemExit("Backup database close block does not match a known 0034 state.")

    patch_0035_parts_dir = ROOT / "source" / "patches" / "0035-parts"
    patch_0035_parts = sorted(patch_0035_parts_dir.glob("*.b64"))
    expected_patch_0035_parts = ["00.b64", "01.b64", "02.b64", "03.b64"]
    if [part.name for part in patch_0035_parts] != expected_patch_0035_parts:
        raise SystemExit("Player UI patch parts are incomplete or unexpected.")
    encoded_patch_0035 = []
    expected_patch_0035_part_sha256 = {
        "00.b64": "93d10863a42f4d7117322ee8593d6f0f1b046dbab1e0847af8a7d990cb094007",
        "01.b64": "8791e7f949fb8ef2d0b8fe05ad2a7446842b68c692945abed9ca5b09ce04cc91",
        "02.b64": "45ffc25911bd5cd369f801d92df3483f589c210504e1128f5d6e2e4b5d80f5f5",
        "03.b64": "b741427940742195ff3bc1cb19378ae15dd9fe96fe1748d0245dd93530d7a2ea",
    }
    for part in patch_0035_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != expected_patch_0035_part_sha256[part.name]:
            raise SystemExit(f"Player UI patch {part.name} checksum mismatch: {actual}")
        encoded_patch_0035.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0035 = base64.b64decode(
            "".join(encoded_patch_0035), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid player UI patch base64: {exc}") from exc
    actual_patch_0035_sha256 = sha256(compressed_patch_0035)
    if actual_patch_0035_sha256 != "a038f7970d6d9b42e234427fb6578e4530f20ef37ec2f466bbc4c0efd2679317":
        raise SystemExit(
            f"Player UI patch checksum mismatch: {actual_patch_0035_sha256}"
        )
    try:
        patch_0035 = gzip.decompress(compressed_patch_0035)
    except (OSError, EOFError) as exc:
        raise SystemExit(f"Player UI patch is not a valid gzip payload: {exc}") from exc
    apply_patch(output, patch_0035, "0035 richer player controls and settings panel")

    patch_0036_parts_dir = ROOT / "source" / "patches" / "0036-parts"
    patch_0036_parts = sorted(patch_0036_parts_dir.glob("*.b64"))
    expected_patch_0036_parts = ["00.b64", "01.b64"]
    if [part.name for part in patch_0036_parts] != expected_patch_0036_parts:
        raise SystemExit("Player display settings patch parts are incomplete or unexpected.")
    encoded_patch_0036 = []
    expected_patch_0036_part_sha256 = {
        "00.b64": "d63aaa32fb95f12a070094b2b087e53ad88c3fbec19cc15efb2069c0d7b4619d",
        "01.b64": "b4b93a2558022fd68071f43222038561195cd199f27219fc2356bedac207f3b6",
    }
    for part in patch_0036_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != expected_patch_0036_part_sha256[part.name]:
            raise SystemExit(f"Player display settings patch {part.name} checksum mismatch: {actual}")
        encoded_patch_0036.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0036 = base64.b64decode(
            "".join(encoded_patch_0036), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid player display settings patch base64: {exc}") from exc
    actual_patch_0036_sha256 = sha256(compressed_patch_0036)
    if actual_patch_0036_sha256 != "73cccc5c3ef5caacf86597e34c13aaef69aff2e828525d696208e9eed88957d1":
        raise SystemExit(
            f"Player display settings patch checksum mismatch: {actual_patch_0036_sha256}"
        )
    try:
        patch_0036 = gzip.decompress(compressed_patch_0036)
    except (OSError, EOFError) as exc:
        raise SystemExit(
            f"Player display settings patch is not a valid gzip payload: {exc}"
        ) from exc
    apply_patch(output, patch_0036, "0036 aspect ratio and subtitle appearance controls")

    patch_0037_parts_dir = ROOT / "source" / "patches" / "0037-parts"
    patch_0037_parts = sorted(patch_0037_parts_dir.glob("*.b64"))
    expected_patch_0037_parts = [f"{index:02d}.b64" for index in range(6)]
    if [part.name for part in patch_0037_parts] != expected_patch_0037_parts:
        raise SystemExit("Persistent player preferences patch parts are incomplete or unexpected.")
    encoded_patch_0037 = []
    expected_patch_0037_part_sha256 = {
        "00.b64": "c8adb85223c959876978e6a3a8aac7f499528b825b1517ba1f93d2d453f48184",
        "01.b64": "3846dfa16476bdf2319b729431a514f87914a5a8d9606f7a3f904345f80dc3b6",
        "02.b64": "601d13cc42b6ce90a5d46dcc36d0e54e88c37ed50c4f61e78a9b44899ae82cca",
        "03.b64": "8409db4cd02ee4fcd5562f147c632854817288106bb38884ce3d170e7135cf5d",
        "04.b64": "6570a3363300a4a647b99bd4b3680e1adbdaf00f9db7763eae255e52250dec2c",
        "05.b64": "eb6bd526e560854322b29839e7e00d6c19023584e83b30a2a0627e477ba93f66",
    }
    for part in patch_0037_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != expected_patch_0037_part_sha256[part.name]:
            raise SystemExit(f"Persistent player preferences patch {part.name} checksum mismatch: {actual}")
        encoded_patch_0037.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0037 = base64.b64decode(
            "".join(encoded_patch_0037), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid persistent player preferences patch base64: {exc}") from exc
    actual_patch_0037_sha256 = sha256(compressed_patch_0037)
    if actual_patch_0037_sha256 != "61cc1f2cabdcae7996d8cc6bb1e7a976d3c105d19ae7f57f38455b59e9fea149":
        raise SystemExit(
            f"Persistent player preferences patch checksum mismatch: {actual_patch_0037_sha256}"
        )
    try:
        patch_0037 = gzip.decompress(compressed_patch_0037)
    except (OSError, EOFError) as exc:
        raise SystemExit(
            f"Persistent player preferences patch is not a valid gzip payload: {exc}"
        ) from exc
    apply_patch(output, patch_0037, "0037 persistent player display preferences and keyboard controls")

    patch_0038 = verified_gzip_patch(
        ROOT / "source" / "patches" / "0038-player-platform-import.patch.gz.b64",
        "bb783064ef38586054e47d843057e54f8f5759b7c12f8eab31d7df5fcc7ab0e7",
        "Player platform import fix",
    )
    apply_patch(output, patch_0038, "0038 import Flutter platform target helpers")

    patch_0039_parts_dir = ROOT / "source" / "patches" / "0039-parts"
    patch_0039_parts = sorted(patch_0039_parts_dir.glob("*.b64"))
    expected_patch_0039_parts = ["00.b64", "01.b64"]
    if [part.name for part in patch_0039_parts] != expected_patch_0039_parts:
        raise SystemExit("Player keyboard focus patch parts are incomplete or unexpected.")
    expected_patch_0039_part_sha256 = {
        "00.b64": "a67a761a161a2a05383d5c0748d9011a61a7abba83eaa4275dd36a7cbc785063",
        "01.b64": "afcb73bc58ced3d3013a2e8ba2ea19dc94aeba49777cc58bff5fcc116dc1e997",
    }
    encoded_patch_0039 = []
    for part in patch_0039_parts:
        raw = part.read_bytes()
        actual = sha256(raw)
        if actual != expected_patch_0039_part_sha256[part.name]:
            raise SystemExit(f"Player keyboard focus patch {part.name} checksum mismatch: {actual}")
        encoded_patch_0039.append(raw.decode("ascii").strip())
    try:
        compressed_patch_0039 = base64.b64decode(
            "".join(encoded_patch_0039), validate=True
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid player keyboard focus patch base64: {exc}") from exc
    actual_patch_0039_sha256 = sha256(compressed_patch_0039)
    if actual_patch_0039_sha256 != "cf949aab9ff06a6109be75379a0bbd5030f404ef672e14f021041fa4dc7e61d5":
        raise SystemExit(
            f"Player keyboard focus patch checksum mismatch: {actual_patch_0039_sha256}"
        )
    try:
        patch_0039 = gzip.decompress(compressed_patch_0039)
    except (OSError, EOFError) as exc:
        raise SystemExit(f"Player keyboard focus patch is not a valid gzip payload: {exc}") from exc
    apply_patch(output, patch_0039, "0039 player keyboard focus and immersive lifecycle safety")





    for backup in output.rglob("*.orig"):
        backup.unlink()
    if not (output / "pubspec.yaml").is_file():
        raise SystemExit("Reconstructed source has no pubspec.yaml.")
    for relative in ("tool/build_android_preview.sh", "tool/build_macos_preview.sh"):
        path = output / relative
        if not path.is_file() or not (path.stat().st_mode & 0o111):
            raise SystemExit(f"Required executable is missing: {relative}")
    print(f"Reconstructed and patched Flutter project at {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("local-media-client"),
        help="empty directory for the reconstructed Flutter project",
    )
    reconstruct(parser.parse_args().output)


if __name__ == "__main__":
    main()
