import logging
from multiprocessing import Queue as ProcessQueue
from typing import Callable

from bailiff.core.config import settings
from bailiff.core.logging import setup_logging
from bailiff.features.diarization.engine import DiarizationEngine

logger = logging.getLogger("bailiff.features.diarization.service")


class DiarizationService:
    """
    Service wrapper for running the DiarizationEngine.

    Initialize and runs the diarization engine in a separate process.
    """
    def __init__(self, 
                 input_queue: ProcessQueue, 
                 output_queue: ProcessQueue,
                 engine_factory: Callable[..., DiarizationEngine] | None = None):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.engine_factory = engine_factory or (
            lambda iq, oq: DiarizationEngine(
                iq, oq,
                threshold=settings.diarization.threshold,
                inertia_weight=settings.diarization.inertia_weight,
            )
        )

    def run(self):
        logger.info("Starting diarization service")
        engine = self.engine_factory(self.input_queue, self.output_queue)
        logger.info("Diarization engine initialized, streaming...")
        engine.run()
        logger.info("Diarization service stopped")


def run_diarization_service(
        input_queue: ProcessQueue, 
        output_queue: ProcessQueue,
        log_file: str | None = None):
    setup_logging(log_file=log_file)
    service = DiarizationService(input_queue, output_queue)
    service.run()
