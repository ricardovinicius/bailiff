from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)

class AppConfig(BaseSettings):
    """
    Configuration for general application settings.
    """
    log_file: str = "bailiff.log"
    log_level: str = "INFO"
    data_dir: str = "data"

class AudioConfig(BaseSettings):
    """
    Configuration for audio processing and ingestion.
    """
    sample_rate: int = 16000
    chunk_size: int = 512
    vad_threshold: float = 0.5
    silence_limit: float = 1.0 # seconds
    speech_pad_ms: int = 200 # ms

class ModelsConfig(BaseSettings):
    """
    Configuration for AI models (LLMs, embeddings, etc.).
    """
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: Optional[SecretStr] = Field(default="dummy")
    llm_assistant: str = "llama-3.1-8b-instant"
    llm_digestion: str = "llama-3.3-70b-versatile"
    llm_summary: str = "llama-3.1-70b-versatile"
    voice_embedding: str = "speechbrain/spkrec-ecapa-voxceleb"

class DiarizationConfig(BaseSettings):
    """
    Configuration for speaker diarization.
    """
    threshold: float = 0.5
    inertia_weight: float = 0.1
    merge_timeout: float = 8.0
    segment_timeout: float = 3.0

class TranscriptionConfig(BaseSettings):
    """
    Configuration for audio transcription.
    """
    model_size: str = "deepdml/faster-whisper-large-v3-turbo-ct2"
    device: str = "cuda"
    compute_type: str = "float16"


class Settings(BaseSettings):
    """
    Global application settings, aggregating all module configurations.
    """
    app: AppConfig
    audio: AudioConfig
    models: ModelsConfig
    diarization: DiarizationConfig
    transcription: TranscriptionConfig

    class Config:
        env_prefix = "BAILIFF_"
        env_nested_delimiter = "__"
        env_file = ".env"
        env_file_encoding = "utf-8"
        yaml_file = "config.yaml"
        extra = "ignore"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

_settings_instance = None

def load_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

settings = load_settings()
