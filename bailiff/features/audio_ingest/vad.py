import logging

import torch
import numpy as np

logger = logging.getLogger("bailiff.audio.vad")


class VADEngine:
    def __init__(self, model_name: str = "snakers4/silero-vad", 
                 threshold: float = 0.6, 
                 sample_rate: int = 16000):
        self.model, self.utils = torch.hub.load(model_name, 
                                                model='silero_vad', 
                                                force_reload=False,
                                                onnx=False)
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.to_tensor = lambda x: torch.from_numpy(x)

        logger.info("VAD engine loaded: model=%s, threshold=%.2f, sample_rate=%d",
                     model_name, threshold, sample_rate)
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Detect speech in an audio chunk.
        Returns True if speech is detected, False otherwise.
        """
        audio_tensor = self.to_tensor(audio_chunk.flatten())
        speech_prob = self.model(audio_tensor, self.sample_rate).item()

        return speech_prob > self.threshold