"""Publish to Mastodon.

Requires a Mastodon account and an application access token.
"""
from __future__ import annotations

import logging

from mastodon import Mastodon

logger = logging.getLogger(__name__)


def publish_to_mastodon(
    api_base_url: str,
    access_token: str,
    post_text: str,
) -> None:
    """Publish a toot.

    If any credential is empty, skips execution.
    """
    if not all([api_base_url, access_token]):
        logger.warning("Missing Mastodon credentials. Skipping Mastodon publish.")
        return

    logger.info("Publishing to Mastodon...")
    
    try:
        client = Mastodon(
            access_token=access_token,
            api_base_url=api_base_url,
        )
        
        response = client.status_post(post_text)
        if response and 'id' in response:
            logger.info("Posted to Mastodon successfully. Post ID: %s", response['id'])
        else:
            logger.info("Posted to Mastodon successfully.")
    except Exception as exc:
        logger.error("Failed to post to Mastodon: %s", exc)
        raise
