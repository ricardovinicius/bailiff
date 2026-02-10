"""
Temporary main script — wires audio ingestion → transcription and prints results.
"""

import logging
import signal
import sys
from multiprocessing import Process, Queue as ProcessQueue

from bailiff.core.config import AudioConfig
from bailiff.core.logging import setup_logging
from bailiff.features.audio_ingest.service import run_ingest_service
from bailiff.features.transcription.service import run_transcription_service

logger = logging.getLogger("bailiff.main")


def main():
    setup_logging()
    logger.info("Starting Bailiff pipeline")

    # Queues that connect the stages
    audio_queue: ProcessQueue = ProcessQueue()          # ingestion → transcription
    transcription_queue: ProcessQueue = ProcessQueue()  # transcription → consumer

    # Spawn child processes
    ingest_proc = Process(
        target=run_ingest_service,
        args=(audio_queue, AudioConfig()),
        name="audio-ingest",
    )
    transcription_proc = Process(
        target=run_transcription_service,
        args=(audio_queue, transcription_queue),
        name="transcription",
    )

    ingest_proc.start()
    transcription_proc.start()

    logger.info("All services started — listening for transcriptions…")

    # Graceful shutdown on Ctrl+C
    def _shutdown(sig, frame):
        logger.info("Shutting down…")
        # Send poison pills so child loops exit cleanly
        audio_queue.put(None)
        transcription_queue.put(None)
        ingest_proc.join(timeout=5)
        transcription_proc.join(timeout=5)
        if ingest_proc.is_alive():
            ingest_proc.terminate()
        if transcription_proc.is_alive():
            transcription_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Main loop: read transcription results and print them
    try:
        while True:
            segment = transcription_queue.get()
            if segment is None:
                break
            logger.info(
                "[%.1fs – %.1fs] %s",
                segment.start_time,
                segment.end_time,
                segment.text,
            )
    except KeyboardInterrupt:
        _shutdown(None, None)


if __name__ == "__main__":
    main()
