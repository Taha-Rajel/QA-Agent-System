"""OpenRouter vision request helper."""

import base64

import requests

from config import MODEL_NAME, OPENROUTER_API_KEY, OPENROUTER_BASE_URL
from tools.log_tool import log_step


def analyze_image(file_path: str, prompt: str) -> str:
    """Send a screenshot and prompt to the configured vision model."""
    if not OPENROUTER_API_KEY:
        return "ERROR: OPENROUTER_API_KEY is missing."

    log_step(f"Asking vision model to review {file_path}")
    with open(file_path, "rb") as image_file:
        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Return a short result in this format: "
                            "PASS or FAIL, then one sentence reason.\n\n"
                            f"Context: {prompt}"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
    }
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json=payload,
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"{exc}; response body: {response.text}") from exc

    content = response.json()["choices"][0]["message"]["content"].strip()
    if not content:
        raise RuntimeError(f"{MODEL_NAME} returned an empty vision response.")
    return content
