"""CLI.   python -m src.main <command>

Commands:
  login      QR se Telegram login (session save hota hai)
  list       DRY-RUN: channel ke ZIP archives list karo (kuch download nahi hota)
  process    --all  ya  --ids 12 15   (chuni hui ZIPs download + extract)
  selftest   Offline test (Telegram ki zarurat nahi)
"""
from __future__ import annotations

import argparse
import asyncio
import sys


def _size(n: int) -> str:
    return f"{n / (1024 * 1024):.1f} MB"


async def _login() -> int:
    from .config import load_settings
    from .telegram_auth import telegram_session
    s = load_settings()
    async with telegram_session(s) as client:
        me = await client.get_me()
        print(f"\nLogin OK: {me.first_name or 'account'} (session saved: workspace/sessions/)")
    return 0


async def _list() -> int:
    from .channel_reader import list_zip_messages, resolve_channel
    from .config import load_settings
    from .manifest import Manifest
    from .telegram_auth import telegram_session
    s = load_settings()
    manifest = Manifest(s.manifest_path, s.workspace)
    async with telegram_session(s) as client:
        ch = await resolve_channel(client, s.channel_name, s.channel_id)
        zips = await list_zip_messages(client, ch)
    print(f"\nChannel: {ch.title} (id {ch.id}) - {len(zips)} ZIP mile  [DRY-RUN: kuch download nahi hua]\n")
    print(f"{'msg_id':>8}  {'size':>10}  {'date':<10}  {'status':<10}  filename")
    for z in zips:
        rec = manifest.get(ch.id, z.message_id)
        status = rec["status"] if rec else "new"
        d = z.date.strftime("%Y-%m-%d") if z.date else "-"
        print(f"{z.message_id:>8}  {_size(z.size):>10}  {d:<10}  {status:<10}  {z.filename}")
    print("\nAgla step: python -m src.main process --all   (ya --ids 12 15)")
    return 0


async def _process(args) -> int:
    from .channel_reader import list_zip_messages, resolve_channel
    from .config import load_settings
    from .manifest import Manifest
    from .pipeline import process_archive
    from .telegram_auth import telegram_session
    if not args.all and not args.ids:
        print("Pehle 'list' chalao, phir '--all' ya '--ids 12 15' do.")
        return 2
    s = load_settings()
    manifest = Manifest(s.manifest_path, s.workspace)
    async with telegram_session(s) as client:
        ch = await resolve_channel(client, s.channel_name, s.channel_id)
        manifest.set_channel(ch.id, ch.title)
        zips = await list_zip_messages(client, ch)
        if args.ids:
            wanted = set(args.ids)
            missing = wanted - {z.message_id for z in zips}
            if missing:
                print(f"Ye message IDs ZIP me nahi mile: {sorted(missing)}")
            zips = [z for z in zips if z.message_id in wanted]
        results = {}
        for z in zips:
            results[z.message_id] = await process_archive(client, ch, z, s, manifest, force=args.force)
    print("\nSummary:")
    for mid, st in results.items():
        print(f"  {mid}: {st}")
    print(f"Manifest: {s.manifest_path}")
    return 0 if all(v in ("completed", "skipped") for v in results.values()) else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m src.main", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    sub.add_parser("list")
    sub.add_parser("selftest")
    pr = sub.add_parser("process")
    pr.add_argument("--all", action="store_true", help="saari ZIPs (jo complete nahi hain)")
    pr.add_argument("--ids", type=int, nargs="+", help="specific message IDs")
    pr.add_argument("--force", action="store_true", help="complete ho chuki ZIP ko dobara process karo")
    args = p.parse_args(argv)

    try:
        if args.cmd == "selftest":
            from .selftest import run
            return run()
        coro = {"login": _login, "list": _list}.get(args.cmd)
        return asyncio.run(coro() if coro else _process(args))
    except KeyboardInterrupt:
        print("\nRoka gaya (Ctrl+C). Manifest me adhoori ZIP 'downloading/extracting' dikhegi, dobara chalao.")
        return 130
    except Exception as e:  # noqa: BLE001
        name = type(e).__name__
        if name in {"ConfigError", "AuthError", "ChannelError", "ManifestError"}:
            print(f"\nERROR: {e}")
            return 1
        raise


if __name__ == "__main__":
    sys.exit(main())
