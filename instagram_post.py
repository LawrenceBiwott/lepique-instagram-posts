"""
Instagram Auto-Poster
---------------------
Posts photos/videos to Instagram every hour using rotating captions.
Uses the Instagram Graph API (requires a Business or Creator account).

Setup: See SETUP_GUIDE.md for credentials and configuration instructions.
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION — reads from env vars (set as GitHub Secrets)
# ─────────────────────────────────────────────
ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.environ.get("INSTAGRAM_USER_ID", "17841402201496454").strip()

# Base URL for media hosted on GitHub raw content.
# Media files in the media/ folder will be served from here.
GITHUB_RAW_BASE = os.environ.get(
    "MEDIA_BASE_URL",
    "https://raw.githubusercontent.com/LawrenceBiwott/lepique-instagram-posts/main/media"
).rstrip("/")

# Paths (relative to this script)
BASE_DIR       = Path(__file__).parent
CAPTIONS_FILE  = BASE_DIR / "captions.json"
MEDIA_FOLDER   = BASE_DIR / "media"
LOG_FILE       = BASE_DIR / "post_log.txt"
STATE_FILE     = BASE_DIR / "state.json"

# Supported file types
IMAGE_EXTS     = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS     = {".mp4", ".mov"}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    """Load persistent state (which caption/media index we're on)."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"caption_index": 0, "media_index": 0}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_captions() -> list:
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["captions"]


def get_next_caption(state: dict) -> dict:
    captions = load_captions()
    if not captions:
        raise ValueError("No captions found in captions.json!")

    idx = state["caption_index"] % len(captions)
    caption = captions[idx]
    state["caption_index"] = (idx + 1) % len(captions)
    return caption


def get_next_media(state: dict) -> Path | None:
    """Get the next media file from the media folder (rotates through all files)."""
    MEDIA_FOLDER.mkdir(exist_ok=True)

    all_files = sorted([
        p for p in MEDIA_FOLDER.iterdir()
        if p.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS)
    ])

    if not all_files:
        return None

    idx = state["media_index"] % len(all_files)
    media = all_files[idx]
    state["media_index"] = (idx + 1) % len(all_files)
    return media


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS


def ensure_config():
    if not ACCESS_TOKEN:
        raise ValueError(
            "INSTAGRAM_ACCESS_TOKEN is missing. Add it as a GitHub Secret or environment variable."
        )

    if not IG_USER_ID:
        raise ValueError(
            "INSTAGRAM_USER_ID is missing. Add it as a GitHub Secret or environment variable."
        )


# ─────────────────────────────────────────────
# INSTAGRAM API CALLS
# ─────────────────────────────────────────────

BASE_URL = "https://graph.instagram.com/v19.0"


def create_image_container(image_url: str, caption: str) -> str:
    """Step 1 for images: create a media container."""
    resp = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )

    if not resp.ok:
        print(resp.text)

    resp.raise_for_status()
    return resp.json()["id"]


def create_video_container(video_url: str, caption: str) -> str:
    """Step 1 for videos/Reels: create a media container."""
    resp = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )

    if not resp.ok:
        print(resp.text)

    resp.raise_for_status()
    return resp.json()["id"]


def wait_for_container(container_id: str, max_wait: int = 300):
    """Poll until the media container is ready. Videos can take longer to process."""
    for _ in range(max_wait // 5):
        resp = requests.get(
            f"{BASE_URL}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN,
            },
            timeout=15,
        )

        if not resp.ok:
            print(resp.text)

        resp.raise_for_status()
        status = resp.json().get("status_code", "")

        if status == "FINISHED":
            return True

        if status == "ERROR":
            raise RuntimeError(f"Container processing failed: {resp.json()}")

        time.sleep(5)

    raise TimeoutError("Media container did not finish processing in time.")


def publish_container(container_id: str) -> str:
    """Step 2: publish the container to Instagram."""
    resp = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )

    if not resp.ok:
        print(resp.text)

    resp.raise_for_status()
    return resp.json()["id"]


# ─────────────────────────────────────────────
# MAIN POST FUNCTION
# ─────────────────────────────────────────────

def post_to_instagram():
    ensure_config()
    log("─── Starting Instagram post ───")

    state = load_state()

    # Get caption
    caption_obj = get_next_caption(state)
    full_caption = caption_obj["text"]

    if caption_obj.get("hashtags"):
        full_caption += "\n\n" + caption_obj["hashtags"]

    log(f"Caption: {full_caption[:80]}...")

    # Get media
    media_path = get_next_media(state)

    if not media_path:
        log("⚠️ No media files found in the 'media/' folder. Add photos/videos and retry.")
        save_state(state)
        return

    log(f"Media: {media_path.name}")

    # Build public URL from the media filename.
    # Files in the media/ folder are served via GitHub raw content.
    media_url = f"{GITHUB_RAW_BASE}/{media_path.name}"
    log(f"Media URL: {media_url}")

    # Create container
    if is_video(media_path):
        container_id = create_video_container(media_url, full_caption)
        log(f"Video/Reel container created: {container_id}. Waiting for processing...")
        wait_for_container(container_id)
    else:
        container_id = create_image_container(media_url, full_caption)
        log(f"Image container created: {container_id}")

    # Publish
    post_id = publish_container(container_id)
    log(f"✅ Posted successfully! Instagram post ID: {post_id}")

    save_state(state)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    try:
        post_to_instagram()
    except Exception as e:
        log(f"❌ Error: {e}")
        raise

