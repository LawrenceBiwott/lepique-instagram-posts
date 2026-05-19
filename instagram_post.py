"""
Instagram Auto-Poster
Posts photos/videos/Reels automatically to Instagram.
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()

IG_USER_ID = os.environ.get(
    "INSTAGRAM_USER_ID",
    "17841402201496454"
).strip()

GITHUB_RAW_BASE = os.environ.get(
    "MEDIA_BASE_URL",
    "https://raw.githubusercontent.com/LawrenceBiwott/lepique-instagram-posts/main/media"
).rstrip("/")

# Paths
BASE_DIR = Path(__file__).parent

CAPTIONS_FILE = BASE_DIR / "captions.json"
MEDIA_FOLDER = BASE_DIR / "media"
LOG_FILE = BASE_DIR / "post_log.txt"
STATE_FILE = BASE_DIR / "state.json"

# Supported file types
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".mov"}

# Instagram API
BASE_URL = "https://graph.facebook.com/v19.0"


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "caption_index": 0,
        "media_index": 0
    }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────────
# CAPTIONS
# ─────────────────────────────────────────────

def load_captions():
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["captions"]


def get_next_caption(state):
    captions = load_captions()

    if not captions:
        raise ValueError("No captions found.")

    idx = state["caption_index"] % len(captions)

    caption = captions[idx]

    state["caption_index"] = (idx + 1) % len(captions)

    return caption


# ─────────────────────────────────────────────
# MEDIA
# ─────────────────────────────────────────────

def get_next_media(state):

    MEDIA_FOLDER.mkdir(exist_ok=True)

    log(f"Checking media folder: {MEDIA_FOLDER.resolve()}")

    all_files = sorted([
        p for p in MEDIA_FOLDER.glob("*")
        if p.is_file()
        and p.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS)
    ])

    log(f"Found {len(all_files)} media files")

    for f in all_files:
        log(f"Detected file: {f.name}")

    if not all_files:
        return None

    idx = state.get("media_index", 0) % len(all_files)

    media = all_files[idx]

    state["media_index"] = (idx + 1) % len(all_files)

    return media


def is_video(path):
    return path.suffix.lower() in VIDEO_EXTS


# ─────────────────────────────────────────────
# CONFIG CHECK
# ─────────────────────────────────────────────

def ensure_config():

    if not ACCESS_TOKEN:
        raise ValueError(
            "INSTAGRAM_ACCESS_TOKEN missing."
        )

    if not IG_USER_ID:
        raise ValueError(
            "INSTAGRAM_USER_ID missing."
        )


# ─────────────────────────────────────────────
# INSTAGRAM API
# ─────────────────────────────────────────────

def create_image_container(image_url, caption):

    response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )

    print(response.text)

    response.raise_for_status()

    return response.json()["id"]


def create_video_container(video_url, caption):

    response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )

    print(response.text)

    response.raise_for_status()

    return response.json()["id"]


def wait_for_container(container_id):

    log("Waiting for Instagram processing...")

    for _ in range(60):

        response = requests.get(
            f"{BASE_URL}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN
            },
            timeout=30
        )

        data = response.json()

        status = data.get("status_code")

        log(f"Container status: {status}")

        if status == "FINISHED":
            return True

        if status == "ERROR":
            raise Exception(f"Instagram processing failed: {data}")

        time.sleep(5)

    raise TimeoutError("Instagram processing timeout.")


def publish_container(container_id):

    response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )

    print(response.text)

    response.raise_for_status()

    return response.json()["id"]


# ─────────────────────────────────────────────
# MAIN POST FUNCTION
# ─────────────────────────────────────────────

def post_to_instagram():

    ensure_config()

    log("─── Starting Instagram post ───")

    state = load_state()

    # Caption
    caption_obj = get_next_caption(state)

    full_caption = caption_obj["text"]

    if caption_obj.get("hashtags"):
        full_caption += "\n\n" + caption_obj["hashtags"]

    log(f"Caption: {full_caption[:80]}")

    # Media
    media_path = get_next_media(state)

    if not media_path:
        log("⚠️ No media files found in media folder.")
        return

    log(f"Selected media: {media_path.name}")

    media_url = f"{GITHUB_RAW_BASE}/{media_path.name}"

    log(f"Media URL: {media_url}")

    # Create container
    if is_video(media_path):

        log("Uploading video/reel...")

        container_id = create_video_container(
            media_url,
            full_caption
        )

        wait_for_container(container_id)

    else:

        log("Uploading image...")

        container_id = create_image_container(
            media_url,
            full_caption
        )

    log(f"Container ID: {container_id}")

    # Publish
    post_id = publish_container(container_id)

    log(f"✅ Successfully posted to Instagram")
    log(f"Instagram Post ID: {post_id}")

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
