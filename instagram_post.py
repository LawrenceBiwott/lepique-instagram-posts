"""
Instagram + Facebook + TikTok Auto-Poster
Posts photos/videos/Reels to Instagram feed & Stories,
Facebook Page feed & Stories, and TikTok (videos only).
"""
import os
import json
import time
import subprocess
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

# TikTok credentials
TIKTOK_CLIENT_KEY    = os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
TIKTOK_REFRESH_TOKEN = os.environ.get("TIKTOK_REFRESH_TOKEN", "").strip()

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
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}

# API base URLs
IG_BASE_URL      = "https://graph.instagram.com/v21.0"
FB_BASE_URL      = "https://graph.facebook.com/v21.0"
TIKTOK_BASE_URL  = "https://open.tiktokapis.com/v2"
TIKTOK_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB per chunk

# Minimum minutes between posts (prevents double-posting when cron runs every 10 min)
MIN_POST_INTERVAL_MINUTES = 55

# Set to 'true' via workflow_dispatch input to bypass the interval guard
FORCE_POST = os.environ.get("FORCE_POST", "false").strip().lower() == "true"

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
    return {"caption_index": 0, "posted_files": [], "tiktok_posted_videos": [], "tiktok_caption_index": 0}

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

def get_next_tiktok_caption(state):
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    captions = data.get("tiktok_captions", [])
    if not captions:
        raise ValueError("No tiktok_captions found in captions.json.")
    idx = state.get("tiktok_caption_index", 0) % len(captions)
    caption = captions[idx]
    state["tiktok_caption_index"] = (idx + 1) % len(captions)
    return caption["text"]

# ─────────────────────────────────────────────
# MEDIA
# ─────────────────────────────────────────────
def get_next_media(state):
    log(f"Checking media folder: {MEDIA_FOLDER}")

    if not MEDIA_FOLDER.exists():
        log("media/ folder not found.")
        return None

    # Build file list — newest additions first (git history), fallback to mtime
    all_files = []
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only", "--format=", "--", "media/"],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        seen = set()
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line:
                fname = Path(line).name
                fpath = MEDIA_FOLDER / fname
                if fpath.exists() and fpath.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS):
                    if fname not in seen:
                        seen.add(fname)
                        all_files.append(fpath)
        if all_files:
            log(f"Found {len(all_files)} media files (newest-first by git history)")
        else:
            raise Exception("Git log returned no files")
    except Exception as e:
        log(f"Git ordering unavailable ({e}) — falling back to mtime sort")
        all_files = sorted(
            [p for p in MEDIA_FOLDER.iterdir()
             if p.is_file() and p.suffix.lower() in (IMAGE_EXTS | VIDEO_EXTS)],
            key=lambda p: p.stat().st_mtime, reverse=True
        )
        log(f"Found {len(all_files)} media files by mtime")

    if not all_files:
        log("No supported media files found in media/")
        return None

    log(f"Latest 5: {[f.name for f in all_files[:5]]}")

    # Always post the newest unposted file first
    posted = set(state.get("posted_files", []))
    selected = None
    for f in all_files:
        if f.name not in posted:
            selected = f
            break

    # All files have been posted — reset cycle
    if selected is None:
        log(f"All {len(all_files)} files posted — resetting cycle, starting from newest.")
        posted = set()
        state["posted_files"] = []
        selected = all_files[0]

    posted.add(selected.name)
    state["posted_files"] = list(posted)
    return selected

def get_next_tiktok_video(state):
    """Pick the next unposted video for TikTok — newest to oldest by mtime, then cycle."""
    if not MEDIA_FOLDER.exists():
        return None

    # Sort all videos newest-first by file modification time
    all_videos = sorted(
        [p for p in MEDIA_FOLDER.iterdir()
         if p.is_file() and p.suffix.lower() in VIDEO_EXTS],
        key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not all_videos:
        log("ℹ️  TikTok: no video files found in media/")
        return None

    log(f"TikTok: {len(all_videos)} videos found (newest → oldest): "
        f"{[v.name for v in all_videos]}")

    posted = set(state.get("tiktok_posted_videos", []))
    selected = None
    for f in all_videos:
        if f.name not in posted:
            selected = f
            break

    if selected is None:
        log(f"TikTok: all {len(all_videos)} videos posted — resetting cycle, starting from newest.")
        state["tiktok_posted_videos"] = []
        selected = all_videos[0]

    posted.add(selected.name)
    state["tiktok_posted_videos"] = list(posted)
    log(f"TikTok selected video: {selected.name}")
    return selected

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

def prepare_story_image(media_path):
    """
    Resize image to 9:16 (1080x1920) with blurred background fill,
    commit to GitHub as media/story_temp.jpg, wait for CDN, return URL.
    Falls back to original feed URL on any error.
    The workflow's final step does git pull --rebase before pushing,
    so this mid-run commit no longer conflicts with the state save.
    """
    original_url = build_media_url(media_path)
    try:
        from PIL import Image, ImageFilter

        STORY_W, STORY_H = 1080, 1920

        img = Image.open(media_path).convert("RGB")
        orig_w, orig_h = img.size

        # Already 9:16 — nothing to do
        if orig_w == STORY_W and orig_h == STORY_H:
            log("Story image already 9:16 — skipping resize.")
            return original_url

        # Scale foreground to fit inside canvas
        scale = min(STORY_W / orig_w, STORY_H / orig_h)
        fg_w = int(orig_w * scale)
        fg_h = int(orig_h * scale)
        foreground = img.resize((fg_w, fg_h), Image.LANCZOS)

        # Blurred background: scale to fill, blur, crop
        bg_scale = max(STORY_W / orig_w, STORY_H / orig_h)
        bg_w = int(orig_w * bg_scale)
        bg_h = int(orig_h * bg_scale)
        background = img.resize((bg_w, bg_h), Image.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=30))
        left = (bg_w - STORY_W) // 2
        top  = (bg_h - STORY_H) // 2
        background = background.crop((left, top, left + STORY_W, top + STORY_H))

        # Paste foreground centred
        paste_x = (STORY_W - fg_w) // 2
        paste_y = (STORY_H - fg_h) // 2
        background.paste(foreground, (paste_x, paste_y))

        story_path = MEDIA_FOLDER / "story_temp.jpg"
        background.save(story_path, "JPEG", quality=92)
        log(f"Story image resized to {STORY_W}x{STORY_H} -> story_temp.jpg")

        # Commit and push — workflow final step uses git pull --rebase to handle this
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "add", str(story_path)], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "chore: story temp image [skip ci]"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
        log("story_temp.jpg pushed. Waiting 15s for CDN...")
        time.sleep(15)

        story_url = f"{GITHUB_RAW_BASE}/story_temp.jpg"
        log(f"Story URL: {story_url}")
        return story_url

    except Exception as e:
        log(f"Story resize failed ({e}) — using original image for Story.")
        return original_url


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
# TIKTOK API
# ─────────────────────────────────────────────
def tiktok_get_access_token():
    """Exchange the stored refresh token for a fresh 24-hour access token."""
    resp = requests.post(
        f"{TIKTOK_BASE_URL}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key":     TIKTOK_CLIENT_KEY,
            "client_secret":  TIKTOK_CLIENT_SECRET,
            "grant_type":     "refresh_token",
            "refresh_token":  TIKTOK_REFRESH_TOKEN,
        },
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("error"):
        raise Exception(f"TikTok token refresh failed: {result}")
    data = result.get("data", result)
    token = data.get("access_token", "")
    if not token:
        raise Exception(f"No access_token in TikTok refresh response: {result}")
    return token


def tiktok_query_creator_info(access_token):
    """Fetch creator info — confirms the account is ready to post."""
    resp = requests.post(
        f"{TIKTOK_BASE_URL}/post/publish/creator_info/query/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("error", {}).get("code", "ok") != "ok":
        raise Exception(f"TikTok creator info failed: {result}")
    return result.get("data", {})


def tiktok_init_video_upload(access_token, file_size, caption):
    """Tell TikTok we're about to upload — returns publish_id and upload_url."""
    # Chunk size must not exceed the file size (TikTok rejects oversized chunks)
    chunk_size    = min(TIKTOK_CHUNK_SIZE, file_size)
    total_chunks  = max(1, (file_size + chunk_size - 1) // chunk_size)

    resp = requests.post(
        f"{TIKTOK_BASE_URL}/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title":                caption[:2200],
                "privacy_level":        "PUBLIC_TO_EVERYONE",
                "disable_duet":         False,
                "disable_comment":      False,
                "disable_stitch":       False,
            },
            "source_info": {
                "source":             "FILE_UPLOAD",
                "video_size":         file_size,
                "chunk_size":         chunk_size,
                "total_chunk_count":  total_chunks,
            }
        },
        timeout=30
    )
    print(resp.text)
    resp.raise_for_status()
    result = resp.json()
    if result.get("error", {}).get("code", "ok") != "ok":
        raise Exception(f"TikTok upload init failed: {result}")
    data = result["data"]
    return data["publish_id"], data["upload_url"], chunk_size, total_chunks


def tiktok_upload_video_chunks(upload_url, video_path, file_size, chunk_size, total_chunks):
    """Stream video to TikTok's upload server, one chunk at a time."""
    with open(video_path, "rb") as f:
        for idx in range(total_chunks):
            start_byte = idx * chunk_size
            chunk_data = f.read(chunk_size)
            end_byte   = start_byte + len(chunk_data) - 1

            content_range = f"bytes {start_byte}-{end_byte}/{file_size}"
            log(f"  TikTok chunk {idx + 1}/{total_chunks}: {content_range}")

            put_resp = requests.put(
                upload_url,
                headers={
                    "Content-Range":  content_range,
                    "Content-Length": str(len(chunk_data)),
                    "Content-Type":   "video/mp4",
                },
                data=chunk_data,
                timeout=120
            )
            if put_resp.status_code not in (200, 201, 206):
                raise Exception(
                    f"TikTok chunk {idx + 1} upload failed "
                    f"({put_resp.status_code}): {put_resp.text}"
                )


def tiktok_poll_status(access_token, publish_id):
    """Poll until TikTok confirms the post is live (or fails)."""
    log("Waiting for TikTok to process the video...")
    terminal_ok  = {"PUBLISH_COMPLETE"}
    terminal_bad = {"FAILED", "ERROR"}

    for attempt in range(36):          # up to ~6 minutes
        resp = requests.post(
            f"{TIKTOK_BASE_URL}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={"publish_id": publish_id},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        status = result.get("data", {}).get("status", "UNKNOWN")
        log(f"  TikTok status ({attempt + 1}): {status}")

        if status in terminal_ok:
            return True
        if status in terminal_bad:
            raise Exception(f"TikTok publish failed: {result}")
        time.sleep(10)

    raise TimeoutError("TikTok processing timed out after 6 minutes.")


def tiktok_init_story_upload(access_token, file_size):
    """Initialize a TikTok Story video upload using the post_to_story flag."""
    # Chunk size must not exceed the file size (TikTok rejects oversized chunks)
    chunk_size   = min(TIKTOK_CHUNK_SIZE, file_size)
    total_chunks = max(1, (file_size + chunk_size - 1) // chunk_size)

    resp = requests.post(
        f"{TIKTOK_BASE_URL}/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "privacy_level":   "PUBLIC_TO_EVERYONE",
                "post_to_story":   True,
                "disable_duet":    False,
                "disable_comment": False,
                "disable_stitch":  False,
            },
            "source_info": {
                "source":            "FILE_UPLOAD",
                "video_size":        file_size,
                "chunk_size":        chunk_size,
                "total_chunk_count": total_chunks,
            }
        },
        timeout=30
    )
    print(resp.text)
    resp.raise_for_status()
    result = resp.json()
    if result.get("error", {}).get("code", "ok") != "ok":
        raise Exception(f"TikTok Story upload init failed: {result}")
    data = result["data"]
    return data["publish_id"], data["upload_url"], chunk_size, total_chunks


def post_tiktok_story(media_path, access_token):
    """Upload a video as a TikTok Story (runs after the regular feed post)."""
    log("--- Posting to TikTok Story ---")
    try:
        file_size = media_path.stat().st_size
        log(f"Initialising TikTok Story upload ({file_size / 1024 / 1024:.1f} MB)...")
        publish_id, upload_url, chunk_size, total_chunks = tiktok_init_story_upload(
            access_token, file_size
        )
        log(f"TikTok Story publish_id: {publish_id}")

        tiktok_upload_video_chunks(upload_url, media_path, file_size, chunk_size, total_chunks)
        log("Story chunks uploaded.")

        tiktok_poll_status(access_token, publish_id)
        log(f"✅ TikTok Story live! publish_id: {publish_id}")

    except Exception as e:
        log(f"⚠️  TikTok Story post failed (feed post not affected): {e}")


def post_to_tiktok(media_path, caption):
    """
    Post a video to TikTok feed + Story using the Content Posting API (Direct Post).
    media_path is always a video — selected independently via get_next_tiktok_video().

    Notes:
      • Until your TikTok Developer app passes TikTok's audit, new posts will
        be visible only to you. Apply at:
        https://developers.tiktok.com/application/content-posting-api
    """
    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET or not TIKTOK_REFRESH_TOKEN:
        log("⚠️  TikTok credentials not configured — skipping TikTok.")
        return

    if media_path is None:
        log("ℹ️  TikTok: no video available to post.")
        return

    log("--- Posting to TikTok ---")
    try:
        # 1. Fresh access token (24-hour lifetime)
        log("Refreshing TikTok access token...")
        access_token = tiktok_get_access_token()
        log("✅ TikTok access token ready.")

        # 2. Confirm creator account is active
        creator = tiktok_query_creator_info(access_token)
        log(f"TikTok creator: @{creator.get('creator_username', '?')} "
            f"(max duration: {creator.get('max_video_post_duration_sec', '?')}s)")

        # 3. Initialise feed upload
        file_size = media_path.stat().st_size
        log(f"Uploading {media_path.name} ({file_size / 1024 / 1024:.1f} MB) to TikTok...")
        publish_id, upload_url, chunk_size, total_chunks = tiktok_init_video_upload(
            access_token, file_size, caption
        )
        log(f"TikTok publish_id: {publish_id}")

        # 4. Stream video chunks
        tiktok_upload_video_chunks(upload_url, media_path, file_size, chunk_size, total_chunks)
        log("All chunks uploaded.")

        # 5. Wait for TikTok feed post to go live
        tiktok_poll_status(access_token, publish_id)
        log(f"✅ TikTok feed post live! publish_id: {publish_id}")

        # 6. Also post as TikTok Story
        post_tiktok_story(media_path, access_token)

    except Exception as e:
        log(f"⚠️  TikTok post failed (Instagram/Facebook not affected): {e}")


# ─────────────────────────────────────────────
# MAIN POST FUNCTION
# ─────────────────────────────────────────────
def post_to_instagram():
    ensure_config()

    state = load_state()

    # ── Interval guard: skip if posted too recently ──
    last_post_time = state.get("last_post_time")
    if last_post_time and not FORCE_POST:
        elapsed = (datetime.utcnow() - datetime.fromisoformat(last_post_time)).total_seconds() / 60
        if elapsed < MIN_POST_INTERVAL_MINUTES:
            log(f"⏭ Skipping — last post was {elapsed:.0f} min ago (next post in ~{MIN_POST_INTERVAL_MINUTES - elapsed:.0f} min).")
            return
    if FORCE_POST:
        log("⚡ FORCE_POST enabled — bypassing interval guard.")

    log("--- Starting Instagram + Facebook + TikTok post ---")

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
    story_url = prepare_story_image(media_path) if not video_file else media_url
    post_ig_story(story_url, video_file)

    # ── Facebook feed + Stories ──
    post_to_facebook(media_url, full_caption, video_file)

    # ── TikTok (independent video queue + separate caption) ──
    tiktok_video = get_next_tiktok_video(state)
    tiktok_caption = get_next_tiktok_caption(state)
    post_to_tiktok(tiktok_video, tiktok_caption)

    # Record successful post time so the interval guard works correctly
    state["last_post_time"] = datetime.utcnow().isoformat()
    save_state(state)
    log("✅ All done. State saved.")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        post_to_instagram()
    except Exception as e:
        log(f"Error: {e}")
        raise
