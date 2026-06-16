"""Custom Vocode synthesizer for 60db (https://60db.ai) text-to-speech.

60db is not a built-in Vocode provider, so this module implements a synthesizer
that conforms to the exact same contract Vocode's built-in synthesizers fulfil
(`BaseSynthesizer.create_speech_uncached -> SynthesisResult`). It therefore plugs
into the same pipeline slot ElevenLabs occupies today — Twilio, the agent, the
transcriber and the events/metrics layer are all untouched.

It uses 60db's streaming WebSocket TTS API (`wss://api.60db.ai/ws/tts`), which can
emit G.711 mu-law at 8 kHz directly. That is exactly Twilio's telephony format, so
no resampling or transcoding is needed — mirroring the existing ElevenLabs
`experimental_websocket=True` setup.

Protocol (per https://docs.60db.ai/websocket-api/tts):
    client connects with ?apiKey=...
    server -> {"connecting": true, ...}
    server -> {"connection_established": {...}}
    client -> {"create_context": {context_id, voice_id, audio_config, ...}}
    server -> {"context_created": {...}}
    client -> {"send_text": {context_id, text}}
    client -> {"flush_context": {context_id}}
    server -> {"audio_chunk": {context_id, audioContent: <base64>}}   (xN)
    server -> {"flush_completed": {context_id}}
    client -> {"close_context": {context_id}}
    server -> {"context_closed": {...}}  (connection closes)
"""

import asyncio
import base64
import json
from typing import Optional

import websockets
from loguru import logger

from vocode.streaming.models.audio import AudioEncoding
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer, SynthesisResult
from vocode.streaming.utils.create_task import asyncio_create_task_with_done_error_log

# Default streaming WebSocket endpoint for 60db TTS.
SIXTYDB_TTS_WS_URL = "wss://api.60db.ai/ws/tts"

# A single fresh WebSocket is opened per synthesis call, so a constant context id
# is sufficient (there is never more than one context on a given connection).
_CONTEXT_ID = "vocode"


class SixtyDBSynthesizerConfig(SynthesizerConfig, type="synthesizer_sixtydb"):
    """Config for the 60db synthesizer.

    Registered as a Vocode ``TypedModel`` with a unique ``type`` discriminator so it
    round-trips cleanly through the Redis config manager (the call config is
    serialized to JSON and rebuilt inside the telephony server process). It inherits
    ``sampling_rate`` and ``audio_encoding`` from ``SynthesizerConfig``.
    """

    api_key: str
    voice_id: str
    speed: float = 1.0
    stability: int = 50
    similarity: int = 75
    enhance: bool = True
    ws_url: str = SIXTYDB_TTS_WS_URL
    # Seconds to wait for the connection_established handshake before giving up.
    connect_timeout_seconds: float = 10.0


class SixtyDBSynthesizer(BaseSynthesizer[SixtyDBSynthesizerConfig]):
    """Streams audio from 60db's WebSocket TTS API into Vocode's pipeline."""

    def __init__(self, synthesizer_config: SixtyDBSynthesizerConfig):
        super().__init__(synthesizer_config)
        self.api_key = synthesizer_config.api_key
        self.voice_id = synthesizer_config.voice_id
        self.speed = synthesizer_config.speed
        self.stability = synthesizer_config.stability
        self.similarity = synthesizer_config.similarity
        self.ws_url = synthesizer_config.ws_url
        self.connect_timeout_seconds = synthesizer_config.connect_timeout_seconds

        # Map Vocode's audio encoding onto 60db's audio_config. MULAW/8000 is the
        # telephony path used by this project; LINEAR16 is supported for completeness.
        if synthesizer_config.audio_encoding == AudioEncoding.MULAW:
            self.audio_encoding_name = "MULAW"
            self.sample_rate_hertz = 8000  # 60db MULAW supports 8 kHz only.
        elif synthesizer_config.audio_encoding == AudioEncoding.LINEAR16:
            self.audio_encoding_name = "LINEAR16"
            self.sample_rate_hertz = synthesizer_config.sampling_rate
        else:
            raise ValueError(
                f"60db synthesizer does not support audio encoding "
                f"{synthesizer_config.audio_encoding}"
            )

    async def create_speech_uncached(
        self,
        message: BaseMessage,
        chunk_size: int,
        is_first_text_chunk: bool = False,
        is_sole_text_chunk: bool = False,
    ) -> SynthesisResult:
        chunk_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()
        asyncio_create_task_with_done_error_log(
            self._stream_to_queue(message.text, chunk_size, chunk_queue),
        )
        return SynthesisResult(
            self.chunk_result_generator_from_queue(chunk_queue),
            # ~150 wpm is the same speech-rate estimate Vocode uses for ElevenLabs;
            # it lets the conversation track how much of the message has been spoken
            # when the caller interrupts.
            lambda seconds: self.get_message_cutoff_from_voice_speed(message, seconds, 150),
        )

    async def _stream_to_queue(
        self,
        text: str,
        chunk_size: int,
        chunk_queue: "asyncio.Queue[Optional[bytes]]",
    ) -> None:
        """Open a WebSocket, synthesize ``text``, and push ``chunk_size`` audio frames.

        Pushes a terminating ``None`` sentinel so ``chunk_result_generator_from_queue``
        ends cleanly, in every exit path (success or failure).
        """
        url = f"{self.ws_url}?apiKey={self.api_key}"
        buffer = bytearray()
        try:
            async with websockets.connect(url) as ws:
                await self._await_connection(ws)

                await ws.send(
                    json.dumps(
                        {
                            "create_context": {
                                "context_id": _CONTEXT_ID,
                                "voice_id": self.voice_id,
                                "audio_config": {
                                    "audio_encoding": self.audio_encoding_name,
                                    "sample_rate_hertz": self.sample_rate_hertz,
                                },
                                "speed": self.speed,
                                "stability": self.stability,
                                "similarity": self.similarity,
                            }
                        }
                    )
                )
                await ws.send(
                    json.dumps({"send_text": {"context_id": _CONTEXT_ID, "text": text}})
                )
                await ws.send(json.dumps({"flush_context": {"context_id": _CONTEXT_ID}}))

                async for raw in ws:
                    message = json.loads(raw)
                    if "audio_chunk" in message:
                        audio_b64 = message["audio_chunk"].get("audioContent")
                        if audio_b64:
                            buffer.extend(base64.b64decode(audio_b64))
                            # Emit fixed-size frames; keep the remainder buffered.
                            while len(buffer) >= chunk_size:
                                await chunk_queue.put(bytes(buffer[:chunk_size]))
                                del buffer[:chunk_size]
                    elif "flush_completed" in message:
                        # All audio for the flushed text has been delivered.
                        try:
                            await ws.send(
                                json.dumps({"close_context": {"context_id": _CONTEXT_ID}})
                            )
                        except Exception:
                            pass
                        break
                    elif "error" in message:
                        logger.error(f"60db TTS error: {message['error']}")
                        break
                    # Other frames (connecting/context_created/context_closed) are ignored.
        except Exception:
            logger.exception("60db TTS websocket synthesis failed")
        finally:
            # Flush any trailing partial frame, then signal end-of-stream.
            if buffer:
                await chunk_queue.put(bytes(buffer))
            await chunk_queue.put(None)

    async def _await_connection(self, ws) -> None:
        """Block until 60db confirms the connection, or raise on auth failure/timeout."""
        deadline_reached = False
        while not deadline_reached:
            raw = await asyncio.wait_for(ws.recv(), timeout=self.connect_timeout_seconds)
            message = json.loads(raw)
            if "connection_established" in message:
                return
            if "error" in message:
                raise RuntimeError(f"60db TTS authentication failed: {message['error']}")
            # {"connecting": true, ...} and anything else -> keep waiting.

    @classmethod
    def get_voice_identifier(cls, synthesizer_config: SixtyDBSynthesizerConfig) -> str:
        """Stable identifier used by Vocode's audio cache to key synthesized phrases."""
        return ":".join(
            (
                "sixtydb",
                synthesizer_config.voice_id,
                str(synthesizer_config.speed),
                str(synthesizer_config.stability),
                str(synthesizer_config.similarity),
                synthesizer_config.audio_encoding,
            )
        )
