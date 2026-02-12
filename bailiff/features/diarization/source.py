import logging
import numpy as np
from bailiff.core.events import AudioChunk
from multiprocessing.queues import Queue as ProcessQueue
from diart.sources import AudioSource

logger = logging.getLogger("bailiff.features.diarization.source")

class StreamSource(AudioSource):
    def __init__(self, audio_queue: ProcessQueue, sample_rate: int = 16000):
        super().__init__("mixed_stream", sample_rate)
        self.audio_queue = audio_queue
        self.sample_rate = sample_rate
        self.epoch_start = None  # wall-clock time of first chunk

    def read(self):
        chunk_count = 0
        while True:
            chunk: AudioChunk = self.audio_queue.get()
            if chunk is None:
                logger.info("Received poison pill, closing stream")
                break

            chunk_count += 1

            # Record the wall-clock time of the very first chunk
            if self.epoch_start is None:
                self.epoch_start = chunk.timestamp
                logger.info("Stream epoch start: %.3f", self.epoch_start)

            waveform = np.expand_dims(chunk.data, axis=0)
            logger.debug(
                "Chunk #%d pushed: shape=%s, samples=%d, duration=%.3fs",
                chunk_count, waveform.shape, waveform.shape[1],
                waveform.shape[1] / self.sample_rate,
            )
            self.stream.on_next(waveform)
        self.stream.on_completed()

    def close(self):
        self.stream.on_completed()