# Telegram Media Project - Part 1 (QR Login + ZIP Extraction)

Ye tool tumhare **apne** Telegram account se QR code se login karta hai, "File Manager" channel ki ZIP files dhundhta hai,
download karke safely extract karta hai, aur images/videos alag folders me rakhkar ek JSON manifest banata hai.
(Part 2/3 - DiskWala, ImgBB/Telegraph - abhi nahi bane.)

## 1. Install (ek baar)

Linux / Mac / Termux:
```bash
cd telegram_media_project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Windows (PowerShell):
```powershell
cd telegram_media_project
py -3 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
Python 3.11+ chahiye (`python3 --version`).

## 2. Secrets sirf `.env` me (chat me kabhi nahi)

1. https://my.telegram.org -> login -> **API development tools** -> app banao -> `api_id` aur `api_hash` milenge.
2. `.env` file kholo aur `API_ID=` / `API_HASH=` ke aage apni values likho.
3. `CHANNEL_NAME=File Manager` (exact naam). Same naam ke kai channels hon to `CHANNEL_ID` bhi daal sakte ho.

`.env` aur `workspace/sessions/` Git me jaate hi nahi (`.gitignore` me hain).

## 3. Commands

| Command | Kya karta hai |
|---|---|
| `python -m src.main selftest` | Offline test (Telegram nahi chahiye) |
| `python -m src.main login` | QR login, session save |
| `python -m src.main list` | **Dry-run**: ZIPs ki list, kuch download nahi |
| `python -m src.main process --ids 12 15` | Sirf chuni hui ZIPs |
| `python -m src.main process --all` | Saari nayi ZIPs |
| `python -m src.main process --all --force` | Complete ZIPs ko bhi dobara |

Tests alag se: `python -m unittest discover -s tests -t .`

## 4. QR login kaise hota hai

`login` chalane par terminal me QR aata hai. Phone me: **Telegram -> Settings -> Devices -> Link Desktop Device** -> scan.
QR ~30 sec me expire hota hai, tool apne aap naya QR dikha deta hai. 2-step password lagta ho to hidden prompt aayega.
Agli baar se session reuse hota hai (QR dobara nahi).

## 5. Expected output

```
$ python -m src.main selftest
== 1) Unit tests ==
................
Ran 16 tests in 0.05s
OK
== 2) End-to-end ZIP extraction demo ==
  image images/album/a.JPG  (73 bytes)
  ...
SELFTEST PASS: 4 media files extracted, manifest: .../manifest.json

$ python -m src.main list
Channel: File Manager (id -100123...) - 2 ZIP mile  [DRY-RUN: kuch download nahi hua]
  msg_id        size  date        status      filename
      12     85.3 MB  2026-10-01  new         photos_set1.zip
      15    420.0 MB  2026-10-05  new         videos_set2.zip

$ python -m src.main process --ids 12
[12] photos_set1.zip: shuru...
  Download: 100%
  Done: 40 images, 0 videos.
```

## 6. Folder structure

```
workspace/downloads/   <channel>_<msgid>_<name>.zip   (original ZIP, kabhi delete nahi)
workspace/extracted/   <channel>_<msgid>_<name>/images/...  aur  /videos/...  (ZIP ka folder structure preserved)
workspace/manifests/manifest.json
workspace/sessions/    Telegram session (chmod 600/700)
```
Sirf images (jpg, jpeg, png, webp, gif, bmp) aur videos (mp4, mkv, mov, webm, avi) extract hote hain; baaki entries skip hoti hain
(count + naam manifest me). Kuch bhi execute nahi hota, aur kuch bhi auto-delete nahi hota.

## 7. Manifest (`workspace/manifests/manifest.json`)

Har archive ke liye: `archive_id` (`channel:message_id`), `archive_filename`, `message_id`, `archive_sha256`, `status`
(`completed / rejected / corrupted / failed`), `errors`, `started_at`, `finished_at`, aur `files[]`: `file_id` (SHA-256),
`type`, `filename`, `size`, `relative_path`, `path`, `original_path_in_zip`. `completed` archive dobara process nahi hota (`--force` se hota hai).

## 8. Safety rules

Path traversal / absolute path / symlink / encrypted entries => poora archive **rejected** (kuch extract hone se pehle).
Limits `.env` me: `MAX_ARCHIVE_MB`, `MAX_EXTRACTED_MB`, `MAX_FILES`, `MAX_COMPRESSION_RATIO`, `MIN_FREE_DISK_MB`.
Download pehle `.part` file me hota hai aur size match hone par hi final naam leta hai.

## 9. Troubleshooting

- **`API_ID / API_HASH nahi mile`** -> `.env` bana hai? Values bharee? File project root me honi chahiye.
- **`ModuleNotFoundError: telethon`** -> venv activate karo, phir `pip install -r requirements.txt`.
- **QR scan hone ke baad bhi atka** -> 2-step password ka prompt check karo; ya `login` dobara chalao.
- **`Channel nahi mila`** -> naam exact (spaces/emoji) ho, aur tumhara account us channel ka member ho. Ya `CHANNEL_ID` daalo.
- **`Multiple matches`** -> number chuno, ya `.env` me `CHANNEL_ID` set karo.
- **FloodWait error** -> Telegram ne thodi der rukne ko kaha; kuch minute baad dobara chalao.
- **Session kharab** -> `workspace/sessions/` ki `.session` file manually delete karke `login` dobara chalao.
- **Manifest kharab** -> tool backup (`.corrupt-<time>`) bana deta hai; dobara chalao.
- **Disk full** -> `workspace/` me jagah banao ya `MIN_FREE_DISK_MB` check karo.
