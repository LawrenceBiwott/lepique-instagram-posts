"""
Sandbox demo: exchanges a real TikTok Login Kit authorization code for an
access token, queries creator info, and publishes one product video via the
Content Posting API (Direct Post, FILE_UPLOAD). Writes the outcome to
demo_result.json so the Studio callback page can display it.

This is used ONLY to produce a genuine, recordable demo of the Login Kit +
Content Posting API flow for TikTok's app review — it mirrors the same
API calls instagram_post.py already makes for the real automated poster.
"""
import json
import os
import time

import requests

CLIENT_KEY = os.environ["TIKTOK_SANDBOX_CLIENT_KEY"]
CLIENT_SECRET = os.environ["TIKTOK_SANDBOX_CLIENT_SECRET"]
AUTH_CODE = os.environ["AUTH_CODE"]
REDIRECT_URI = os.environ["REDIRECT_URI"]
VIDEO_PATH = "media/videos/lepique-video-11-transition.mp4"
CAPTION = ("New arrivals at Lepique Fashions \U0001F456 Platinum Plaza, Shop G16, "
           "Tom Mboya Street, Nairobi. #LepiqueFashions #NairobiFashion #Jeans")

result = {"code": AUTH_CODE, "status": "error", "message": "", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}


def save():
    with open("demo_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


try:
    print("Exchanging authorization code for access token...")
    token_resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        },
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": AUTH_CODE,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    token_data = token_resp.json()
    print("Token response:", {k: v for k, v in token_data.items() if k != "access_token"})

    if "access_token" not in token_data:
        result["message"] = f"Token exchange failed: {token_data}"
        save()
        raise SystemExit(0)

    access_token = token_data["access_token"]

    print("Querying creator info...")
    creator_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        timeout=30,
    )
    creator_data = creator_resp.json()
    print("Creator info:", creator_data)
    creator = creator_data.get("data", {})
    result["creator_username"] = creator.get("creator_username")
    result["creator_nickname"] = creator.get("creator_nickname")

    if not os.path.exists(VIDEO_PATH):
        result["message"] = f"Video file not found: {VIDEO_PATH}"
        save()
        raise SystemExit(0)

    video_size = os.path.getsize(VIDEO_PATH)
    print(f"Initializing direct post ({video_size} bytes)...")

    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={
            "post_info": {
                "title": CAPTION,
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    init_data = init_resp.json()
    print("Init response:", init_data)

    if "data" not in init_data or "upload_url" not in init_data["data"]:
        result["message"] = f"Init failed: {init_data.get('error', init_data)}"
        save()
        raise SystemExit(0)

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]
    result["publish_id"] = publish_id

    print("Uploading video bytes...")
    with open(VIDEO_PATH, "rb") as f:
        video_bytes = f.read()

    upload_resp = requests.put(
        upload_url,
        headers={
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            "Content-Type": "video/mp4",
        },
        data=video_bytes,
        timeout=120,
    )
    print("Upload status:", upload_resp.status_code, upload_resp.text[:500])

    status = "PROCESSING_UPLOAD"
    for attempt in range(12):
        time.sleep(5)
        status_resp = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={"publish_id": publish_id},
            timeout=30,
        )
        status_data = status_resp.json()
        print(f"Status check {attempt + 1}:", status_data)
        status = status_data.get("data", {}).get("status", status)
        if status in ("PUBLISH_COMPLETE", "FAILED"):
            break

    result["publish_status"] = status
    if status == "PUBLISH_COMPLETE":
        result["status"] = "success"
    else:
        result["status"] = "error"
        result["message"] = f"Publish did not complete (status: {status})"

    save()

except SystemExit:
    raise
except Exception as e:
    result["message"] = str(e)
    print("ERROR:", e)
    save()
