from bailiff.core.events import TranscriptionSegment
import time
import logging
from typing import Callable
from multiprocessing import Process, Queue as ProcessQueue

from bailiff.features.transcription.engine import WhisperEngine
from bailiff.core.events import AudioChunk

logger = logging.getLogger("bailiff.transcription.service")

# TODO: Add a hallucination detection mechanism to avoid non-sense transcriptions, such as "Subtitles by "

class TranscriptionService:
    def __init__(self, 
                 input_queue: ProcessQueue, 
                 output_queue: ProcessQueue, 
                 engine_factory: Callable[[], WhisperEngine] = lambda: WhisperEngine(language=None)):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.engine_factory = engine_factory

    def run(self):
        logger.info("Starting transcription service")

        self.engine = self.engine_factory()
        self.engine.load()

        logger.info("Transcription service started")
        
        while True:
            try:
                chunk: AudioChunk = self.input_queue.get()

                if chunk is None:
                    logger.info("Transcription service stopped")
                    break

                start_time = time.time()
                text = self.engine.transcribe(chunk.data)
                
                if text:
                    end_time = time.time()
                    duration = end_time - start_time

                    segment = TranscriptionSegment(
                        text=text,
                        start_time=chunk.timestamp,
                        end_time=chunk.timestamp + chunk.duration,
                        duration=duration,
                    )

                    logger.info("Transcription: %s (%.2fs)", text, duration)
                    self.output_queue.put(segment)
            except Exception as e:
                logger.error("Error in transcription service: %s", e)
                continue

def run_transcription_service(input_queue: ProcessQueue, output_queue: ProcessQueue, log_file: str | None = None):
    from bailiff.core.logging import setup_logging
    setup_logging(log_file=log_file)
    service = TranscriptionService(input_queue, output_queue)
    service.run()