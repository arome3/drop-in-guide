#!/usr/bin/env python3
# Drop-in Guide scene captioning skill.
# Provides a synchronous `describe_scene` @skill that runs OpenAI Vision on
# the current camera frame and returns a one-sentence description string.
# This avoids the async-image-update issue with dimOS's default `observe` skill,
# which returns an Image object via a separate tool_update Claude doesn't wait for.

import base64
import io
from typing import Any

import cv2
import numpy as np
from openai import OpenAI

from dimos.agents.annotation import skill
from dimos.core.core import rpc
from dimos.core.module import Module
from dimos.core.stream import In
from dimos.msgs.sensor_msgs.Image import Image
from dimos.utils.logging_config import setup_logger

logger = setup_logger()

VISION_MODEL = "gpt-4o-mini"
CAPTION_PROMPT = (
    "You are helping prime a quadruped robot's spatial memory. Look at this "
    "camera frame and identify THE MOST SALIENT object a visitor might want "
    "to navigate to (printer, copier, kitchen, meeting room, door, charger, "
    "vending machine, water cooler, desk, etc.). Skip people, generic walls, "
    "and floor. Reply in ONE short sentence describing the object and where "
    "it is in the frame (left/center/right). Example: 'A tall white printer "
    "on the right side of the frame.' If nothing salient is visible, reply: "
    "'No salient object visible in this view.'"
)


class SceneCaptionSkill(Module):
    """Captions current camera frame via OpenAI Vision for the priming loop."""

    color_image: In[Image]
    _latest_frame: Image | None = None

    @rpc
    def start(self) -> None:
        super().start()
        self._openai = OpenAI()
        self.color_image.subscribe(self._on_image)

    @rpc
    def stop(self) -> None:
        super().stop()

    def _on_image(self, image: Image) -> None:
        self._latest_frame = image

    def _encode_jpeg_b64(self, img: Image) -> str:
        data = img.data
        if data.dtype != np.uint8:
            data = (data * 255).astype(np.uint8) if data.max() <= 1.0 else data.astype(np.uint8)
        bgr = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
        ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            raise RuntimeError("failed to encode frame to JPEG")
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    @skill
    def describe_scene(self) -> str:
        """Look at the current camera frame and describe the most salient object.

        Use this DURING PRIMING to figure out what to propose tagging. Returns
        a single English sentence describing one notable object visible right
        now, or 'No salient object visible in this view.' if there is nothing
        worth tagging.

        Call this BEFORE proposing a tag with `speak`.
        """
        if self._latest_frame is None:
            return "No camera frame received yet."

        try:
            b64 = self._encode_jpeg_b64(self._latest_frame)
        except Exception as e:
            logger.error(f"describe_scene encode failed: {e}", exc_info=True)
            return f"Error encoding camera frame: {e}"

        try:
            resp = self._openai.chat.completions.create(
                model=VISION_MODEL,
                max_tokens=80,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": CAPTION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                        ],
                    }
                ],
            )
            caption = (resp.choices[0].message.content or "").strip()
            return caption or "No salient object visible in this view."
        except Exception as e:
            logger.error(f"describe_scene VL call failed: {e}", exc_info=True)
            return f"Error captioning frame: {e}"
