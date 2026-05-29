from __future__ import annotations

from typing import Any


IMAGE_GENERATION_KEYWORDS = (
    "generate image",
    "create image",
    "draw",
    "render",
    "make an image",
    "make a picture",
    "picture of",
    "photo of",
    "illustration",
    "poster",
    "visual",
    "text-to-image",
    "image-to-image",
)


def normalize_input_images(context: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return uploaded images in one normalized list.

    The UI historically sent a single image via image_base64/image_mime_type. This
    also accepts a future-proof context["images"] list.
    """
    context = context or {}
    images: list[dict[str, Any]] = []

    for item in context.get("images", []) or []:
        if not isinstance(item, dict):
            continue
        image_base64 = item.get("image_base64") or item.get("base64")
        image_url = item.get("url") or item.get("image_url")
        if not image_base64 and not image_url:
            continue
        images.append(
            {
                "image_base64": image_base64,
                "image_url": image_url,
                "mime_type": item.get("mime_type") or item.get("image_mime_type") or "image/jpeg",
                "name": item.get("name") or item.get("filename") or "uploaded-image",
                "reference_type": item.get("reference_type") or "character",
            }
        )

    if context.get("image_base64") or context.get("image_url"):
        images.append(
            {
                "image_base64": context.get("image_base64"),
                "image_url": context.get("image_url"),
                "mime_type": context.get("image_mime_type", "image/jpeg"),
                "name": context.get("image_name", "uploaded-image"),
                "reference_type": context.get("image_reference_type", "character"),
            }
        )

    return images


def provider_supports_vision(
    provider: str | None,
    model: str | None,
    context: dict[str, Any] | None = None,
) -> bool:
    context = context or {}
    explicit = context.get("llm_supports_vision")
    if isinstance(explicit, bool):
        return explicit

    provider_name = (provider or "").lower()
    model_name = (model or "").lower()
    combined = f"{provider_name} {model_name}"

    # MiniMax's OpenAI-compatible text endpoint currently rejects image/audio
    # inputs; its image capabilities live behind a separate image_generation API.
    if provider_name == "minimax":
        return False

    vision_markers = (
        "vl",
        "vision",
        "gpt-4o",
        "gpt-4.1",
        "o3",
        "o4",
        "gemini",
        "claude-3",
        "claude-sonnet",
        "claude-opus",
    )
    return any(marker in combined for marker in vision_markers)


def build_user_content_for_model(
    query: str,
    context: dict[str, Any] | None,
    provider: str | None,
    model: str | None,
) -> tuple[str | list[dict[str, Any]], list[str], bool]:
    images = normalize_input_images(context)
    if not images:
        return query, [], False

    if provider_supports_vision(provider, model, context):
        content: list[dict[str, Any]] = [{"type": "text", "text": query}]
        for image in images:
            if image.get("image_url"):
                image_url = image["image_url"]
            else:
                image_url = f"data:{image['mime_type']};base64,{image['image_base64']}"
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        return content, [], True

    warning = (
        "An image was uploaded, but the selected chat model endpoint does not "
        "support image understanding. The answer is based on text only."
    )
    text_only_query = (
        f"{query}\n\n"
        "[Uploaded image note: an image was provided by the user, but this "
        "provider/model endpoint cannot inspect images. State this limitation "
        "clearly if the answer depends on visual details.]"
    )
    return text_only_query, [warning], False


def wants_image_output(query: str, context: dict[str, Any] | None) -> bool:
    context = context or {}
    mode = str(context.get("image_output_mode", "auto")).lower()
    enabled = context.get("enable_image_output", False)

    if mode in {"never", "off", "false", "none"}:
        return False
    if mode in {"always", "force"}:
        return True
    if not enabled:
        return False

    lowered_query = query.lower()
    return any(keyword in lowered_query for keyword in IMAGE_GENERATION_KEYWORDS)


def stringify_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        return "\n".join(part for part in text_parts if part).strip()
    if content is None:
        return ""
    return str(content).strip()
