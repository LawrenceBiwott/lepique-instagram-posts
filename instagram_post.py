"""
Instagram + Facebook Auto-Poster
Posts photos/videos/Reels to Instagram feed & Stories,
and to Facebook Page feed & Stories.
"""
import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.environ.get(
    "INSTAGRAM_USER_ID",
    "17841402201496454"
).strip()
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()

GITHUB_RAW_BASE = os.environ.get(
    "MEDIA_BASE_URL",
    "https://raw.githubusercontent.com/LawrenceBiwott/lepique-instagram-posts/main/media"
).rstrip("/")

# Paths
BASE_DIR = Path(__file__).resolve().parent
CAPTIONS_FILE = BASE_DIR / "captions.json"
MEDIA_FOLDER = BASE_DIR / "media"
LOG_FILE = BASE_DIR / "post_log.txt"
STATE_FILE = BASE_DIR / "state.json"

# Supported file types
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".mov"}

# API base URLs
IG_BASE_URL = "https://graph.instagram.com/v21.0"
FB_BASE_URL = "https://graph.facebook.com/v21.0"

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
    return {"caption_index": 0, "media_index": 0}

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
        raise ValueError("No captions found in captions.json.")
    idx = state.get("caption_index", 0) % len(captions)
    caption = captions[idx]
    state["caption_index"] = (idx + 1) % len(captions)
    return caption

# ─────────────────────────────────────────────
# MEDIA
# ─────────────────────────────────────────────
def get_next_media(state):
    log(f"Current working directory: {Path.cwd()}")
    log(f"Script base directory: {BASE_DIR}")
    log(f"Checking media folder: {MEDIA_FOLDER}")

    if not MEDIA_FOLDER.exists():
        log("media folder does not exist.")
        for item in sorted(BASE_DIR.iterdir()):
            log(f"  Root item: {item.name}")
        return None

    # Order by git commit history — newest file added to repo posts first
    import subprocess
    all_files = []
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only", "--format=", "--", "media/"],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line:
                fname = Path(line).name
                fpath = MEDIA_FOLDER / fname
                if fpath.exists() and fpath.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS):
                    if fpath not in all_files:
                        all_files.append(fpath)
        if all_files:
            log(f"Found {len(all_files)} media files (newest-first by git history)")
        else:
            raise Exception("Git log returned no results")
    except Exception as e:
        log(f"Git ordering unavailable ({e}), falling back to mtime sort")
        all_files = sorted([
            p for p in MEDIA_FOLDER.iterdir()
            if p.is_file() and p.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS)
        ], key=lambda p: p.stat().st_mtime, reverse=True)
        log(f"Found {len(all_files)} media files in media/")
    for f in all_files[:5]:
        log(f"  Detected: {f.name}")

    if not all_files:
        log("Files currently inside media/ (all types):")
        for item in sorted(MEDIA_FOLDER.iterdir()):
            log(f"  media item: {item.name} (suffix: {item.suffix})")
        return None

    idx = state.get("media_index", 0) % len(all_files)
    media = all_files[idx]
    state["media_index"] = (idx + 1) % len(all_files)
    return media

def is_video(path):
    return path.suffix.lower() in VIDEO_EXTS

def build_media_url(media_path):
    safe_filename = quote(media_path.name)
    return f"{GITHUB_RAW_BASE}/{safe_filename}"

# ─────────────────────────────────────────────
# CONFIG CHECK
# ─────────────────────────────────────────────
def ensure_config():
    if not ACCESS_TOKEN:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN missing.")
    if not IG_USER_ID:
        raise ValueError("INSTAGRAM_USER_ID missing.")

# ─────────────────────────────────────────────
# INSTAGRAM API
# ─────────────────────────────────────────────
def create_image_container(image_url, caption):
    response = requests.post(
        f"{IG_BASE_URL}/{IG_USER_ID}/media",
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
        f"{IG_BASE_URL}/{IG_USER_ID}/media",
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
            f"{IG_BASE_URL}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN
            },
            timeout=30
        )
        print(response.text)
        response.raise_for_status()
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
        f"{IG_BASE_URL}/{IG_USER_ID}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN
        },
        timeout=30
    )
    print(response.text)
    response.raise_for_status()
    return response.json()["id"]

def create_ig_story_container(media_url, is_video_file):
    """Create an Instagram Stories container."""
    params = {
        "media_type": "STORIES",
        "access_token": ACCESS_TOKEN
    }
    if is_video_file:
        params["video_url"] = media_url
    else:
        params["image_url"] = media_url
    response = requests.post(
        f"{IG_BASE_URL}/{IG_USER_ID}/media",
        params=params,
        timeout=30
    )
    print(response.text)
    response.raise_for_status()
    return response.json()["id"]

def post_ig_story(media_url, is_video_file):
    """Post to Instagram Stories."""
    log("Posting to Instagram Stories...")
    try:
        story_container = create_ig_story_container(media_url, is_video_file)
        wait_for_container(story_container)
        story_id = publish_container(story_container)
        log(f"✅ Instagram Story posted! ID: {story_id}")
    except Exception as e:
        log(f"⚠️ Instagram Story post failed (feed post still succeeded): {e}")

# ─────────────────────────────────────────────
# FACEBOOK API
# ─────────────────────────────────────────────
def post_fb_photo(image_url, caption):
    """Post a photo to the Facebook Page feed."""
    response = requests.post(
        f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
        params={
            "url": image_url,
            "caption": caption,
            "access_token": FB_PAGE_ACCESS_TOKEN
        },
        timeout=30
    )
    print(response.text)
    response.raise_for_status()
    return response.json().get("post_id") or response.json().get("id")

def post_fb_video(video_url, caption):
    """Post a video to the Facebook Page feed."""
    response = requests.post(
        f"{FB_BASE_URL}/{FB_PAGE_ID}/videos",
        params={
            "file_url": video_url,
            "description": caption,
            "access_token": FB_PAGE_ACCESS_TOKEN
        },
        timeout=60
    )
    print(response.text)
    response.raise_for_status()
    return response.json().get("id")

def post_fb_photo_story(image_url):
    """Post a photo to Facebook Page Stories."""
    # Step 1: upload photo (unpublished) to get a photo ID
    upload_resp = requests.post(
        f"{FB_BASE_URL}/{FB_PAGE_ID}/photos",
        params={
            "url": image_url,
            "published": "false",
            "temporary": "true",
            "access_token": FB_PAGE_ACCESS_TOKEN
        },
        timeout=30
    )
    print(upload_resp.text)
    upload_resp.raise_for_status()
    photo_id = upload_resp.json().get("id")

    # Step 2: publish as Story
    story_resp = requests.post(
        f"{FB_BASE_URL}/{FB_PAGE_ID}/photo_stories",
        params={
            "photo_id": photo_id,
            "access_token": FB_PAGE_ACCESS_TOKEN
        },
        timeout=30
    )
    print(story_resp.text)
    story_resp.raise_for_status()
    return story_resp.json().get("post_id") or story_resp.json().get("id")

def post_fb_video_story(video_url):
    """Post a video to Facebook Page Stories (two-step upload)."""
    # Step 1: initialise upload session
    init_resp = requests.post(
        f"{FB_BASE_URL}/{FB_PAGE_ID}/video_stories",
        params={
            "upload_phase": "start",
            "access_token": FB_PAGE_ACCESS_TOKEN
        },
        timeout=30
    )
    print(init_resp.text)
    init_resp.raise_for_status()
    video_id = init_resp.json().get("video_id")

    # Step 2: finish with public URL
    finish_resp = requests.post(
        f"{FB_BASE_URL}/{FB_PAGE_ID}/video_stories",
        params={
            "upload_phase": "finish",
            "video_id": video_id,
            "file_url": video_url,
            "access_token": FB_PAGE_ACCESS_TOKEN
        },
        timeout=60
    )
    print(finish_resp.text)
    finish_resp.raise_for_status()
    return video_id

def post_to_facebook(media_url, caption, is_video_file):
    """Post to Facebook Page feed AND Stories."""
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        log("⚠️ Facebook credentials not set — skipping Facebook post.")
        return

    log("--- Posting to Facebook ---")

    # Feed post
    try:
        if is_video_file:
            log("Uploading video to Facebook feed...")
            fb_post_id = post_fb_video(media_url, caption)
        else:
            log("Uploading photo to Facebook feed...")
            fb_post_id = post_fb_photo(media_url, caption)
        log(f"✅ Facebook feed post successful! ID: {fb_post_id}")
    except Exception as e:
        log(f"⚠️ Facebook feed post failed: {e}")

    # Story
    try:
        if is_video_file:
            log("Posting video to Facebook Stories...")
            story_id = post_fb_video_story(media_url)
        else:
            log("Posting photo to Facebook Stories...")
            story_id = post_fb_photo_story(media_url)
        log(f"✅ Facebook Story posted! ID: {story_id}")
    except Exception as e:
        log(f"⚠️ Facebook Story post failed: {e}")

# ─────────────────────────────────────────────
# MAIN POST FUNCTION
# ─────────────────────────────────────────────
def post_to_instagram():
    ensure_config()
    log("--- Starting Instagram + Facebook post ---")

    state = load_state()

    caption_obj = get_next_caption(state)
    full_caption = caption_obj["text"]
    if caption_obj.get("hashtags"):
        full_caption += "\n\n" + caption_obj["hashtags"]
    log(f"Caption: {full_caption[:80]}")

    media_path = get_next_media(state)
    if not media_path:
        log("No media files found in media folder.")
        save_state(state)
        return

    log(f"Selected media: {media_path.name}")
    media_url = build_media_url(media_path)
    log(f"Media URL: {media_url}")

    video_file = is_video(media_path)

    # ── Instagram feed ──
    if video_file:
        log("Uploading video/reel to Instagram...")
        container_id = create_video_container(media_url, full_caption)
    else:
        log("Uploading image to Instagram...")
        container_id = create_image_container(media_url, full_caption)

    wait_for_container(container_id)
    log(f"Container ID: {container_id}")
    post_id = publish_container(container_id)
    log(f"✅ Instagram feed post successful! ID: {post_id}")

    # ── Instagram Stories ──
    post_ig_story(media_url, video_file)

    # ── Facebook feed + Stories ──
    post_to_facebook(media_url, full_caption, video_file)

    save_state(state)

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        post_to_instagram()
    except Exception as e:
        log(f"Error: {e}")
        raise
