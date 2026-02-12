import logging
import numpy as np

from faster_whisper import WhisperModel

logger = logging.getLogger("bailiff.transcription.engine")

class WhisperEngine:
    def __init__(self, 
                model_size: str = "deepdml/faster-whisper-large-v3-turbo-ct2", 
                device: str = "cuda",
                compute_type: str = "float16",
                language: str | None = None,
                ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.model = None

    def load(self):
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        logger.info("Whisper model loaded: %s", self.model_size)

    def transcribe(self, audio: np.ndarray) -> str:
        if self.model is None:
            raise RuntimeError("Whisper model not loaded. Call load() first.")

        segments, info = self.model.transcribe(
            audio,
            beam_size=5,
            language=self.language,
            condition_on_previous_text=False,
        )
        
        text = " ".join([seg.text for seg in segments]).strip()
        logger.info("Transcription: %s", text)

        return text