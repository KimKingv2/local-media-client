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
