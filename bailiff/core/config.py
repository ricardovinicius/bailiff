from dataclasses import dataclass

# TODO: Probably i should use a .env file to store this config

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_size: int = 512
    vad_threshold: float = 0.5
    vad_model_name: str = "snakers4/silero-vad"
    silence_limit: float = 0.5 # seconds
    speech_pad_ms: int = 200 # ms
