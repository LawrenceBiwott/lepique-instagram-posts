#!/usr/bin/env python3
"""
TikTok OAuth Token Generator — Lepique Fashions
================================================
Run this ONCE on your computer to get the tokens needed for GitHub Actions.

Requirements:
    pip install requests

Usage:
    python get_tiktok_token.py
"""

import webbrowser
import urllib.parse
import secrets
import sys

try:
    import requests
except ImportError:
    print("❌ Missing 'requests'. Run:  pip install requests")
    sys.exit(1)

# ─────────────────────────────────────────────
REDIRECT_URI = "https://www.example.com/callback"
SCOPE = "video.publish,user.info.basic"
# ─────────────────────────────────────────────


def extract_code_from_url(url):
    """Pull the 'code' parameter out of the redirect URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            return params["code"][0]
    except Exception:
        pass
    return None


def main():
    print()
    print("=" * 60)
    print("  TikTok Token Generator — Lepique Fashions")
    print("=" * 60)
    print()
    print("You need your TikTok Sandbox App credentials.")
    print("Find them at: developers.tiktok.com → Lepique Auto-Poster")
    print("              → Sandbox tab → Credentials section")
    print()

    client_key    = input("Paste your Client Key:    ").strip()
    client_secret = input("Paste your Client Secret: ").strip()

    if not client_key or not client_secret:
        print("❌ Both Client Key and Client Secret are required.")
        sys.exit(1)

    state = secrets.token_hex(8)

    # Build TikTok OAuth URL
    auth_url = (
        "https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={urllib.parse.quote(client_key)}"
        f"&scope={urllib.parse.quote(SCOPE)}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&state={state}"
    )

    print()
    print("=" * 60)
    print("  STEP 1: Open this URL in your browser")
    print("=" * 60)
    print()
    print("Opening browser automatically...")
    print("Log in as @lepique_fashions and click Authorize.")
    print()
    print("If browser doesn't open, copy-paste this URL manually:")
    print(auth_url)
    print()

    webbrowser.open(auth_url)

    print("=" * 60)
    print("  STEP 2: Copy the URL from your browser")
    print("=" * 60)
    print()
    print("After clicking Authorize, your browser will go to a page")
    print("that shows an error (that's normal — example.com isn't real).")
    print()
    print("Copy the FULL URL from the browser address bar and paste it below.")
    print("It will look like:")
    print("  https://www.example.com/callback?code=XXXX&state=YYYY")
    print()

    redirect_url = input("Paste the full redirect URL here: ").strip()

    auth_code = extract_code_from_url(redirect_url)

    if not auth_code:
        print()
        print("❌ Could not find the authorization code in that URL.")
        print("   Make sure you copied the full URL from the address bar.")
        print("   It should contain '?code=' in it.")
        sys.exit(1)

    print()
    print(f"✅ Authorization code found! Exchanging for tokens...")

    # Exchange auth code for access + refresh tokens
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key":     client_key,
            "client_secret":  client_secret,
            "code":           auth_code,
            "grant_type":     "authorization_code",
            "redirect_uri":   REDIRECT_URI,
        },
        timeout=30
    )

    if resp.status_code != 200:
        print(f"❌ Token exchange failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    result = resp.json()

    if result.get("error"):
        print(f"❌ TikTok returned an error: {result}")
        sys.exit(1)

    data          = result.get("data", result)
    access_token  = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")
    open_id       = data.get("open_id", "")
    expires_in    = data.get("expires_in", "?")
    refresh_exp   = data.get("refresh_expires_in", "?")

    if not refresh_token:
        print(f"❌ No refresh token in response. Full response:\n{result}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  ✅ SUCCESS! Add these 4 secrets to GitHub:")
    print("  Settings → Secrets and variables → Actions → New secret")
    print("=" * 60)
    print()
    print(f"Secret name:  TIKTOK_CLIENT_KEY")
    print(f"Secret value: {client_key}")
    print()
    print(f"Secret name:  TIKTOK_CLIENT_SECRET")
    print(f"Secret value: {client_secret}")
    print()
    print(f"Secret name:  TIKTOK_OPEN_ID")
    print(f"Secret value: {open_id}")
    print()
    print(f"Secret name:  TIKTOK_REFRESH_TOKEN")
    print(f"Secret value: {refresh_token}")
    print()
    print("=" * 60)
    print(f"  Access token expires:  in {expires_in} seconds (~24 hours)")
    print(f"  Refresh token valid:   {refresh_exp} seconds (~365 days)")
    print()
    print("  ⚠️  Keep these private — never share or commit to git!")
    print("=" * 60)
    print()

    # Save locally for convenience
    output_file = "tiktok_tokens.txt"
    with open(output_file, "w") as f:
        f.write(f"TIKTOK_CLIENT_KEY={client_key}\n")
        f.write(f"TIKTOK_CLIENT_SECRET={client_secret}\n")
        f.write(f"TIKTOK_OPEN_ID={open_id}\n")
        f.write(f"TIKTOK_REFRESH_TOKEN={refresh_token}\n")
        f.write(f"\n# For reference only (expires in ~24h):\n")
        f.write(f"# TIKTOK_ACCESS_TOKEN={access_token}\n")

    print(f"  Tokens also saved to: {output_file}")
    print(f"  Delete this file after adding secrets to GitHub!")
    print()


if __name__ == "__main__":
    main()
