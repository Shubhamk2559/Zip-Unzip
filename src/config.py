"""Settings .env se load hoti hain. Secrets kabhi print nahi hote."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .zip_processor import MB, Limits

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    pass


def _num(name: str, default, cast=int):
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return cast(raw)
    except ValueError as e:
        raise ConfigError(f"{name} ek number hona chahiye (abhi: {raw!r})") from e


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str = field(repr=False)
    session_name: str
    channel_name: str
    channel_id: int | None
    workspace: Path
    limits: Limits

    @property
    def downloads_dir(self) -> Path:
        return self.workspace / "downloads"

    @property
    def extracted_dir(self) -> Path:
        return self.workspace / "extracted"

    @property
    def manifests_dir(self) -> Path:
        return self.workspace / "manifests"

    @property
    def sessions_dir(self) -> Path:
        return self.workspace / "sessions"

    @property
    def manifest_path(self) -> Path:
        return self.manifests_dir / "manifest.json"

    @property
    def session_base(self) -> Path:
        return self.sessions_dir / self.session_name


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    api_id_raw = os.getenv("API_ID", "").strip()
    api_hash = os.getenv("API_HASH", "").strip()
    if not api_id_raw or not api_hash:
        raise ConfigError(
            "API_ID / API_HASH nahi mile. '.env' file me apni values bharo "
            "(my.telegram.org se milti hain). '.env.example' dekho."
        )
    if not api_id_raw.isdigit():
        raise ConfigError("API_ID sirf number hona chahiye.")

    ws = Path(os.getenv("WORKSPACE_DIR", "workspace").strip() or "workspace")
    if not ws.is_absolute():
        ws = PROJECT_ROOT / ws

    cid_raw = os.getenv("CHANNEL_ID", "").strip()
    try:
        channel_id = int(cid_raw) if cid_raw else None
    except ValueError as e:
        raise ConfigError("CHANNEL_ID number hona chahiye (e.g. -1001234567890).") from e

    limits = Limits(
        max_archive_bytes=_num("MAX_ARCHIVE_MB", 2048) * MB,
        max_extracted_bytes=_num("MAX_EXTRACTED_MB", 4096) * MB,
        max_files=_num("MAX_FILES", 10_000),
        max_ratio=_num("MAX_COMPRESSION_RATIO", 200.0, float),
        min_free_bytes=_num("MIN_FREE_DISK_MB", 500) * MB,
    )
    return Settings(
        api_id=int(api_id_raw),
        api_hash=api_hash,
        session_name=os.getenv("SESSION_NAME", "file_manager").strip() or "file_manager",
        channel_name=os.getenv("CHANNEL_NAME", "File Manager").strip() or "File Manager",
        channel_id=channel_id,
        workspace=ws,
        limits=limits,
    )
