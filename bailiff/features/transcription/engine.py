import logging
import numpy as np

from faster_whisper import WhisperModel

logger = logging.getLogger("bailiff.transcription.engine")

class WhisperEngine:
    def __init__(self, 
                model_size: str = "distil-small.en", 
                device: str = "cpu",
                compute_type: str = "int8",
                ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
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
            condition_on_previous_text=False,
        )
        
        text = " ".join([seg.text for seg in segments]).strip()
        logger.info("Transcription: %s", text)

        return text