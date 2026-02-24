"""
Social Media MCP Server – Facebook, Instagram, Twitter/X posting + summaries.

Endpoints:
  POST /post/twitter    – post a tweet (X)
  POST /post/facebook   – post to Facebook Page
  POST /post/instagram  – create Instagram media post
  POST /post/all        – broadcast to all platforms
  GET  /health
"""
import logging
import os
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SocialMCP] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Social Media MCP Server", version="1.0.0")


# ── Models ────────────────────────────────────────────────────────────────────

class PostRequest(BaseModel):
    text: str
    image_url: Optional[str] = None
    require_approval: bool = True


class BroadcastResult(BaseModel):
    twitter: Optional[dict] = None
    facebook: Optional[dict] = None
    instagram: Optional[dict] = None


# ── Twitter/X ─────────────────────────────────────────────────────────────────

def _post_twitter(text: str, image_url: str | None = None) -> dict:
    """Post a tweet via Twitter API v2."""
    bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
    api_key = os.getenv("TWITTER_API_KEY", "")
    api_secret = os.getenv("TWITTER_API_SECRET", "")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET", "")

    try:
        import tweepy
        client = tweepy.Client(
            bearer_token=bearer,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
        response = client.create_tweet(text=text[:280])
        tweet_id = response.data["id"]
        log.info("Tweet posted: %s", tweet_id)
        return {"platform": "twitter", "id": tweet_id, "status": "published", "text": text[:280]}
    except ImportError:
        raise RuntimeError("Install tweepy: pip install tweepy")
    except Exception as exc:
        raise RuntimeError(f"Twitter error: {exc}")


# ── Facebook ──────────────────────────────────────────────────────────────────

def _post_facebook(text: str, image_url: str | None = None) -> dict:
    """Post to a Facebook Page via Graph API."""
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    page_token = os.getenv("FACEBOOK_PAGE_TOKEN", "")

    if not page_id or not page_token:
        raise RuntimeError("FACEBOOK_PAGE_ID and FACEBOOK_PAGE_TOKEN must be set.")

    endpoint = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    payload: dict = {"message": text, "access_token": page_token}
    if image_url:
        # Post photo instead
        endpoint = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        payload["url"] = image_url

    resp = requests.post(endpoint, data=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    post_id = result.get("id", "")
    log.info("Facebook post published: %s", post_id)
    return {"platform": "facebook", "id": post_id, "status": "published"}


# ── Instagram ─────────────────────────────────────────────────────────────────

def _post_instagram(text: str, image_url: str | None = None) -> dict:
    """
    Post to Instagram via Graph API (Business/Creator account required).
    Requires an image URL — Instagram does not support text-only posts.
    """
    ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    if not ig_account_id or not ig_token:
        raise RuntimeError("INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN must be set.")
    if not image_url:
        raise RuntimeError("Instagram requires image_url.")

    # Step 1: Create media container
    create_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
    resp = requests.post(create_url, data={
        "image_url": image_url,
        "caption": text,
        "access_token": ig_token,
    }, timeout=15)
    resp.raise_for_status()
    container_id = resp.json().get("id")

    # Step 2: Publish
    publish_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
    resp2 = requests.post(publish_url, data={
        "creation_id": container_id,
        "access_token": ig_token,
    }, timeout=15)
    resp2.raise_for_status()
    media_id = resp2.json().get("id", "")
    log.info("Instagram post published: %s", media_id)
    return {"platform": "instagram", "id": media_id, "status": "published"}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "social-media-mcp-server"}


@app.post("/post/twitter")
def post_twitter(req: PostRequest):
    try:
        return _post_twitter(req.text, req.image_url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/post/facebook")
def post_facebook(req: PostRequest):
    try:
        return _post_facebook(req.text, req.image_url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/post/instagram")
def post_instagram(req: PostRequest):
    try:
        return _post_instagram(req.text, req.image_url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/post/all")
def broadcast(req: PostRequest):
    """Post to all configured social media platforms."""
    results: dict = {"timestamp": datetime.now().isoformat()}
    for platform, fn in [
        ("twitter", _post_twitter),
        ("facebook", _post_facebook),
        ("instagram", _post_instagram),
    ]:
        try:
            results[platform] = fn(req.text, req.image_url)
        except Exception as exc:
            results[platform] = {"platform": platform, "status": "error", "detail": str(exc)}
            log.error("%s post failed: %s", platform, exc)
    return results


if __name__ == "__main__":
    host = os.getenv("SOCIAL_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("SOCIAL_MCP_PORT", "8005"))
    uvicorn.run(app, host=host, port=port)
