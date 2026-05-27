#!/usr/bin/env python3
# Drop-in Guide speak skill — routes TTS through the Go2's onboard speaker
# via WebRTC AUDIO_HUB_REQ instead of local sounddevice playback.
# Mirrors the upload-and-play pattern from dimos/skills/unitree/unitree_speak.py
# but exposes a Module-level @skill that Claude can call.

import base64
import hashlib
import json
import os
import tempfile
import threading
import time
from typing import Any

import numpy as np
from openai import OpenAI
import soundfile as sf
from unitree_webrtc_connect.constants import RTC_TOPIC

from dimos.agents.annotation import skill
from dimos.core.core import rpc
from dimos.core.module import Module
from dimos.robot.unitree.go2.connection_spec import GO2ConnectionSpec
from dimos.utils.logging_config import setup_logger

logger = setup_logger()

AUDIO_API = {
    "GET_AUDIO_LIST": 1001,
    "SELECT_START_PLAY": 1002,
    "PAUSE": 1003,
    "SET_PLAY_MODE": 1007,
    "UPLOAD_AUDIO_FILE": 2001,
}
PLAY_MODE_NO_CYCLE = "no_cycle"


class DropInGuideSpeakSkill(Module):
    """TTS through the Go2's onboard speaker (replaces local-audio SpeakSkill)."""

    _connection: GO2ConnectionSpec

    @rpc
    def start(self) -> None:
        super().start()
        self._openai = OpenAI()

    @rpc
    def stop(self) -> None:
        super().stop()

    def _webrtc(self, api_id: int, parameter: dict[str, Any] | None = None) -> dict[Any, Any]:
        param = parameter or {}
        return self._connection.publish_request(
            RTC_TOPIC["AUDIO_HUB_REQ"],
            {"api_id": api_id, "parameter": json.dumps(param) if param else "{}"},
        )

    def _generate_wav(self, text: str) -> tuple[bytes, float]:
        """OpenAI TTS -> normalized 22050Hz WAV bytes + duration."""
        resp = self._openai.audio.speech.create(
            model="tts-1", voice="echo", input=text, speed=1.2, response_format="mp3"
        )
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(resp.content)
            mp3_path = f.name
        try:
            arr, sr = sf.read(mp3_path)
            if arr.ndim > 1:
                arr = np.mean(arr, axis=1)
            target_sr = 22050
            if sr != target_sr:
                new_len = int(len(arr) * target_sr / sr)
                arr = np.interp(np.linspace(0, len(arr) - 1, new_len), np.arange(len(arr)), arr)
                sr = target_sr
            arr = arr / np.max(np.abs(arr))
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wf:
                sf.write(wf.name, arr, sr, format="WAV", subtype="PCM_16")
                wav_path = wf.name
            try:
                wav = open(wav_path, "rb").read()
            finally:
                os.unlink(wav_path)
            return wav, float(len(arr)) / sr
        finally:
            os.unlink(mp3_path)

    def _upload(self, wav_data: bytes, filename: str) -> str:
        md5 = hashlib.md5(wav_data).hexdigest()
        b64 = base64.b64encode(wav_data).decode("utf-8")
        chunk_size = 61440
        chunks = [b64[i : i + chunk_size] for i in range(0, len(b64), chunk_size)]
        total = len(chunks)
        logger.info(f"speak: uploading '{filename}' in {total} chunks")
        for i, chunk in enumerate(chunks, 1):
            self._webrtc(
                AUDIO_API["UPLOAD_AUDIO_FILE"],
                {
                    "file_name": filename,
                    "file_type": "wav",
                    "file_size": len(wav_data),
                    "current_block_index": i,
                    "total_block_number": total,
                    "block_content": chunk,
                    "current_block_size": len(chunk),
                    "file_md5": md5,
                    "create_time": int(time.time() * 1000),
                },
            )
        resp = self._webrtc(AUDIO_API["GET_AUDIO_LIST"], {})
        try:
            data_str = (resp or {}).get("data", {}).get("data", "{}")
            audio_list = json.loads(data_str).get("audio_list", [])
            for item in audio_list:
                if item.get("CUSTOM_NAME") == filename:
                    return item.get("UNIQUE_ID")
        except Exception:
            pass
        return filename

    def _play_and_wait(self, uuid: str, duration: float) -> None:
        self._webrtc(AUDIO_API["SET_PLAY_MODE"], {"play_mode": PLAY_MODE_NO_CYCLE})
        time.sleep(0.1)
        self._webrtc(AUDIO_API["SELECT_START_PLAY"], {"unique_id": uuid})

    def _do_speak(self, text: str) -> None:
        try:
            wav, dur = self._generate_wav(text)
            filename = f"speak_{int(time.time() * 1000)}"
            uuid = self._upload(wav, filename)
            self._play_and_wait(uuid, dur)
        except Exception as e:
            logger.error(f"speak failed: {e}", exc_info=True)

    @skill
    def speak(self, text: str) -> str:
        """Speak text out loud through the robot's onboard speaker.

        Use this often. People hear what you speak but cannot read your text. Be concise.

        Args:
            text: The text to speak. Keep to one or two short sentences.
        """
        display = text[:60] + ("..." if len(text) > 60 else "")
        threading.Thread(
            target=self._do_speak, args=(text,), daemon=True, name="DropInGuideSpeak"
        ).start()
        return f"Speaking: '{display}'"
