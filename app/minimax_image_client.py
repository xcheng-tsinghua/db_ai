from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class MiniMaxImageGenerationError(RuntimeError):
    pass


def generate_minimax_images(
    *,
    api_key: str,
    prompt: str,
    input_images: list[dict[str, Any]] | None = None,
    model: str | None = None,
    aspect_ratio: str = "1:1",
    n: int = 1,
    response_format: str = "base64",
    prompt_optimizer: bool = True,
) -> list[dict[str, Any]]:
    if not api_key:
        raise MiniMaxImageGenerationError("MiniMax API key is required for image generation.")

    image_model = model or settings.MINIMAX_IMAGE_MODEL
    count = max(1, min(int(n or 1), 9))
    payload: dict[str, Any] = {
        "model": image_model,
        "prompt": prompt[:1500],
        "aspect_ratio": aspect_ratio,
        "response_format": response_format,
        "n": count,
        "prompt_optimizer": prompt_optimizer,
    }

    references = []
    for image in input_images or []:
        image_file = image.get("image_url") or image.get("image_base64")
        if not image_file:
            continue
        references.append(
            {
                "type": image.get("reference_type", "character"),
                "image_file": image_file,
            }
        )
    if references:
        payload["subject_reference"] = references[:4]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info(
        "Calling MiniMax image generation model=%s aspect_ratio=%s n=%s references=%s",
        image_model,
        aspect_ratio,
        count,
        len(references),
    )
    response = requests.post(
        settings.MINIMAX_IMAGE_GENERATION_URL,
        headers=headers,
        json=payload,
        timeout=settings.IMAGE_REQUEST_TIMEOUT_SECONDS,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise MiniMaxImageGenerationError(response.text) from exc

    data = response.json()
    base_resp = data.get("base_resp") or {}
    if base_resp and base_resp.get("status_code") not in (None, 0, "0"):
        raise MiniMaxImageGenerationError(base_resp.get("status_msg") or str(data))

    output_images: list[dict[str, Any]] = []
    image_data = data.get("data") or {}

    for image_base64 in image_data.get("image_base64", []) or []:
        output_images.append(
            {
                "provider": "minimax",
                "model": image_model,
                "mime_type": "image/jpeg",
                "image_base64": image_base64,
                "url": None,
                "metadata": {"id": data.get("id"), "response_format": "base64"},
            }
        )

    for image_url in image_data.get("image_urls", []) or []:
        output_images.append(
            {
                "provider": "minimax",
                "model": image_model,
                "mime_type": "image/jpeg",
                "image_base64": None,
                "url": image_url,
                "metadata": {"id": data.get("id"), "response_format": "url"},
            }
        )

    return output_images
