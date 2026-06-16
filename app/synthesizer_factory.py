"""Synthesizer factory that teaches the Vocode telephony server about 60db.

Vocode's ``DefaultSynthesizerFactory`` only knows its built-in providers
(ElevenLabs, Azure, Cartesia, ...). To make our custom ``SixtyDBSynthesizer``
usable from a ``SynthesizerConfig``, the ``TelephonyServer`` must be given a factory
that recognises ``SixtyDBSynthesizerConfig`` — exactly the same extension pattern the
repo already uses for ``SpellerAgentFactory`` on the agent side.

Everything that is not a 60db config is delegated to the default factory, so
ElevenLabs (and any other built-in synthesizer) keeps working unchanged.
"""

from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.synthesizer.abstract_factory import AbstractSynthesizerFactory
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer
from vocode.streaming.synthesizer.default_factory import DefaultSynthesizerFactory

from .sixtydb_synthesizer import SixtyDBSynthesizer, SixtyDBSynthesizerConfig


class VoiceBotSynthesizerFactory(AbstractSynthesizerFactory):
    def __init__(self):
        self._default_factory = DefaultSynthesizerFactory()

    def create_synthesizer(
        self,
        synthesizer_config: SynthesizerConfig,
    ) -> BaseSynthesizer:
        if isinstance(synthesizer_config, SixtyDBSynthesizerConfig):
            return SixtyDBSynthesizer(synthesizer_config)
        return self._default_factory.create_synthesizer(synthesizer_config)
