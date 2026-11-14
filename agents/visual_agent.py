"""Visual agent for model-based screenshot evaluation."""

import asyncio

from models import VisualLog
from tools.vision_tool import analyze_image


class VisualAgent:
    async def evaluate(self, screenshot_path: str, context: str):
        """Evaluate a screenshot and return a VisualLog object."""
        try:
            raw = await asyncio.to_thread(analyze_image, screenshot_path, context)
            normalized = raw.strip().upper()
            status = "FAIL" if normalized.startswith(("FAIL", "ERROR")) else "PASS"
            return VisualLog(status=status, reason=raw.strip())
        except Exception as exc:
            return VisualLog(status="FAIL", reason=f"Vision check failed: {exc}")
