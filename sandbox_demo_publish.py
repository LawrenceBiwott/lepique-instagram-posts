"""
Sandbox demo: exchanges a real TikTok Login Kit authorization code for an
access token and queries creator info via the Content Posting API. Writes
the outcome to demo_result.json so the Studio callback page can display it.

NOTE: This intentionally stops after the creator_info query and does not
call video/init. TikTok's Direct Post API restricts unaudited API clients
to posting only to accounts that are set to private at the time of
posting (see https://developers.tiktok.com/doc/content-sharing-guidelines).
The connected account, @lepique_fashions, is a Business account, which
TikTok does not allow to be set to private. Attempting video/init here
would always fail with `unaudited_client_can_only_post_to_private_accounts`
regardless of credentials, so the demo instead ends at a genuine,
successful "connected" state (real OAuth + real creator_info API call)
rather than staging a fake publish result.

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

    if creator_data.get("error", {}).get("code") not in (None, "ok"):
        result["message"] = f"Creator info failed: {creator_data.get('error')}"
        save()
        raise SystemExit(0)

    # Stop here — see module docstring for why video/init is intentionally
    # not attempted in this demo.
    result["status"] = "success"
    result["stage"] = "connected"
    save()

except SystemExit:
    raise
except Exception as e:
    result["message"] = str(e)
    print("ERROR:", e)
    save()
