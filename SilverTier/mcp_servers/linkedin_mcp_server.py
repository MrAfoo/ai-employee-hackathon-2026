"""
LinkedIn MCP Server – auto-posting and content management via LinkedIn API.

Endpoints:
  POST /post          – create a LinkedIn post (text or article)
  GET  /posts         – list recent posts made by this server
  POST /post/approve  – human-in-the-loop: approve a queued post
  POST /post/reject   – reject a queued post
  GET  /health        – health check
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LinkedInMCP] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

app = FastAPI(title="LinkedIn MCP Server", version="1.0.0")

_pending_posts: Dict[str, dict] = {}
_published_posts: list[dict] = []


class PostRequest(BaseModel):
    text: str
    visibility: str = "PUBLIC"          # PUBLIC or CONNECTIONS
    require_approval: bool = True


def _linkedin_headers() -> dict:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def _publish_post(person_urn: str, text: str, visibility: str = "PUBLIC") -> dict:
    """Call LinkedIn UGC Posts API to publish a post."""
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility
        },
    }
    resp = requests.post(
        f"{LINKEDIN_API_BASE}/ugcPosts",
        headers=_linkedin_headers(),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


@app.get("/health")
def health():
    return {"status": "ok", "service": "linkedin-mcp-server"}


@app.post("/post")
def create_post(req: PostRequest):
    """Queue or immediately publish a LinkedIn post."""
    post_id = str(uuid.uuid4())[:8]
    record = {
        "id": post_id,
        "text": req.text,
        "visibility": req.visibility,
        "queued_at": datetime.now().isoformat(),
        "status": "pending" if req.require_approval else "auto_published",
    }

    if req.require_approval:
        _pending_posts[post_id] = record
        log.info("Post queued for approval (id=%s): %.60s...", post_id, req.text)
        return {"post_id": post_id, "status": "pending_approval", "preview": req.text[:100]}

    person_urn = os.getenv("LINKEDIN_PERSON_URN", "")
    if not person_urn:
        raise HTTPException(status_code=400, detail="LINKEDIN_PERSON_URN not configured.")
    try:
        result = _publish_post(person_urn, req.text, req.visibility)
        record["status"] = "published"
        record["linkedin_id"] = result.get("id", "")
        record["published_at"] = datetime.now().isoformat()
        _published_posts.append(record)
        return {"post_id": post_id, "status": "published", "linkedin_id": record["linkedin_id"]}
    except requests.RequestException as exc:
        log.error("LinkedIn post failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/pending")
def list_pending():
    return {"pending": list(_pending_posts.values()), "count": len(_pending_posts)}


@app.post("/approve/{post_id}")
def approve_post(post_id: str):
    """Approve and publish a queued LinkedIn post."""
    if post_id not in _pending_posts:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found.")
    record = _pending_posts.pop(post_id)
    person_urn = os.getenv("LINKEDIN_PERSON_URN", "")
    if not person_urn:
        raise HTTPException(status_code=400, detail="LINKEDIN_PERSON_URN not configured.")
    try:
        result = _publish_post(person_urn, record["text"], record["visibility"])
        record["status"] = "published"
        record["linkedin_id"] = result.get("id", "")
        record["published_at"] = datetime.now().isoformat()
        _published_posts.append(record)
        log.info("Post approved and published: %s", post_id)
        return {"post_id": post_id, "status": "published", "linkedin_id": record["linkedin_id"]}
    except requests.RequestException as exc:
        log.error("Failed to publish approved post: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/reject/{post_id}")
def reject_post(post_id: str, reason: str = "Rejected by human reviewer."):
    """Reject a queued LinkedIn post."""
    if post_id not in _pending_posts:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found.")
    record = _pending_posts.pop(post_id)
    record["status"] = "rejected"
    record["rejected_at"] = datetime.now().isoformat()
    record["rejection_reason"] = reason
    _published_posts.append(record)
    return {"post_id": post_id, "status": "rejected"}


@app.get("/posts")
def list_posts():
    return {"posts": _published_posts, "count": len(_published_posts)}


if __name__ == "__main__":
    host = os.getenv("LINKEDIN_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("LINKEDIN_MCP_PORT", "8002"))
    uvicorn.run(app, host=host, port=port)
