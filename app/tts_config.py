"""Single source of truth for which TTS provider the bot uses.

Selection is driven by the ``TTS_PROVIDER`` environment variable so the two
providers coexist by configuration rather than code edits:

    TTS_PROVIDER=elevenlabs   (default — unchanged existing behavior)
    TTS_PROVIDER=60db         (use 60db instead)

Both inbound (``app/inbound.py``) and outbound (``app/outbound_call.py``) call
``get_synthesizer_config()`` so a single env var flips both call directions
consistently. All voices run at telephony-native MULAW / 8000 Hz.

Importing this module also registers ``SixtyDBSynthesizerConfig`` (via the import
below), which is required for the config type to deserialize inside the telephony
server process when it is read back from Redis.
"""

import os

from loguru import logger

from vocode.streaming.models.audio import AudioEncoding
from vocode.streaming.models.synthesizer import (
    ElevenLabsSynthesizerConfig,
    SynthesizerConfig,
)

from .sixtydb_synthesizer import SixtyDBSynthesizerConfig

# Accepted spellings for selecting 60db via TTS_PROVIDER.
_SIXTYDB_ALIASES = {"60db", "sixtydb", "sixty_db", "sixty-db"}


def get_tts_provider() -> str:
    """Return the normalized provider name: ``"60db"`` or ``"elevenlabs"``."""
    raw = os.getenv("TTS_PROVIDER", "elevenlabs").strip().lower()
    return "60db" if raw in _SIXTYDB_ALIASES else "elevenlabs"


def get_synthesizer_config(experimental_websocket: bool = True) -> SynthesizerConfig:
    """Build the synthesizer config for the configured provider.

    Args:
        experimental_websocket: Only affects ElevenLabs — enables its low-latency
            websocket streaming path (the inbound server uses ``True``). 60db always
            streams over its WebSocket API regardless of this flag.
    """
    provider = get_tts_provider()

    if provider == "60db":
        logger.info("🔊 TTS provider: 60db")
        return SixtyDBSynthesizerConfig(
            api_key=os.environ["SIXTYDB_API_KEY"],
            voice_id=os.environ["SIXTYDB_VOICE_ID"],
            sampling_rate=8000,
            audio_encoding=AudioEncoding.MULAW,
            speed=float(os.getenv("SIXTYDB_SPEED", "1.0")),
            stability=int(os.getenv("SIXTYDB_STABILITY", "50")),
            similarity=int(os.getenv("SIXTYDB_SIMILARITY", "75")),
        )

    logger.info("🔊 TTS provider: ElevenLabs")
    return ElevenLabsSynthesizerConfig(
        api_key=os.environ["ELEVEN_LABS_API_KEY"],
        voice_id=os.environ["ELEVEN_LABS_VOICE_ID"],
        sampling_rate=8000,
        audio_encoding=AudioEncoding.MULAW,
        experimental_streaming=experimental_websocket,
        experimental_websocket=experimental_websocket,
    )
