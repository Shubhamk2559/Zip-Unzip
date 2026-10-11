"""Test ZIPs banane ke helpers (stdlib only)."""
import stat
import zipfile
from pathlib import Path

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


def make_zip(path: Path, entries: dict[str, bytes], compression=zipfile.ZIP_DEFLATED) -> Path:
    with zipfile.ZipFile(path, "w", compression) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return Path(path)


def make_symlink_zip(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        info = zipfile.ZipInfo("link.png")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(info, "/etc/passwd")
    return Path(path)


def sample_entries() -> dict[str, bytes]:
    return {
        "album/a.JPG": PNG + b"1",
        "album/sub/b.png": PNG + b"2",
        "clips/c.mp4": MP4,
        "clips/d.MKV": MP4 + b"x",
        "notes.txt": b"hello",
        "run.sh": b"echo no",
        "__MACOSX/._a.JPG": b"junk",
    }
